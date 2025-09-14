from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from app.v1.utils import parse_xls, to_float_or_none

from app.v1.schemas.schemas import WorkbookParseResponse, FileUploadResponse, BulkGradeUpdate
from app.v1.auth.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import UploadedFile, User, Classroom, Student
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
import logging
import xlrd
import os

print("=== FILE.PY LOADED ===")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__routers/me.py__")

router = APIRouter(
    prefix="/me",
    tags=["me"],
    responses={404: {"description": "Not found"}}
)

# Consonants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = ['.xls', '.xlsx']

# ===============================
# 📁 FILE MANAGEMENT ENDPOINTS
# ===============================
@router.post("/file", summary="upload an XLS file",response_model=FileUploadResponse)
async def upload_file(
                    file: UploadFile = File(...),
                    db: Session = Depends(get_db),
                    current_user: str = Depends(get_current_user)
                    ):
    """
    Endpoint to upload an XLS file with proper validation and error handling.
    """
    logger.info(f"File upload request from user: {current_user}")
    existing_user = db.query(User).filter_by(id=current_user).first()
    if not existing_user:
        logger.error(f"User: {current_user} not found in database")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not registred. Please register first"
        ) 


    # validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
            )

    # Check file extension
    if not file.filename.endswith('.xls'):
        logger.error("Invalid file type. Only .xls files are allowed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .xls files are allowed."
            )
    try:   
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // {1024*1024}} MB")

        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Empty file is provided")

        # Check if user already has a file
        existing_file = db.query(UploadedFile).filter_by(user_id=current_user).first()
        if existing_file:
            logging.warning(f'User {current_user} already has a file {existing_file.file_name}')
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has a file. Delete the existing filefirst"
                )
        
        # Parse XLS file
        try:    
            workbook = xlrd.open_workbook(
                file_contents=content,
                ignore_workbook_corruption=True,
                formatting_info=True
            )
            # from app.v1.utils
            data = parse_xls(workbook)

        except Exception as parse_error:
            logger.error(f"Error parsing XLS file: {str(parse_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= f"Error parsing XLS file: {str(parse_error)}"
            )
        
        # Check the mismatch of academic level
        level_from_file =  data.get('classrooms')[0].get("level")
        level_from_user = db.query(User).filter_by(id=current_user).first().academic_level.value

        logger.info(f"Level from file: {level_from_file}")
        logger.info(f"Level from user: {level_from_user}")

        logger.info(f"{'متوسط' in level_from_file}")
        logger.info(f"{level_from_user == 'secondary'}")

        if ("متوسط" not in level_from_file or level_from_user != "secondary"):
            logger.error(f"Academic level mismatch: {level_from_file} vs {level_from_user}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Academic level mismatch: the level from the file:{level_from_file} vs the level provided by the user:{level_from_user}"
            )        
        # Database transaction
        try:
            # Create uploaded file record
            uploaded_file = UploadedFile(
                user_id = current_user,
                file_name = file.filename,
                storage_path ="placeholder_path.xlsx" # Placeholder path
            )

            logger.info(f'uploaded_file instance {uploaded_file}')
        
            db.add(uploaded_file)
            db.flush() # Get the file_id
            populate_database(db, uploaded_file.file_id, data)    
            db.commit()
            logger.info(f"Successfully processed file: {file.filename} for user: {current_user}")          
        
            return {
                "file_id": str(uploaded_file.file_id),
                "num_classrooms": len(data["classrooms"]),
                "data": data,
                }
    
        except SQLAlchemyError as db_error:
            db.rollback()
            logger.error(f"Database error: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occured while saving file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the file"
        )

def populate_database(db: Session, file_id:str , data:dict) -> None:
    """
    Populate database with parsed XLS data.
    """
    classrooms: list = data.get('classrooms', [])

    if not classrooms:
        logger.warning(f'No classrooms found in parsed data')
        return 
    # 
    #
    #
    #
    # THE CLASSROOM MODEL
    # ===============================
    # class Classroom(Base):
    # __tablename__ = "classrooms"

    # classroom_id = Column(Integer, primary_key=True,index=True) 
    # file_id = Column(UUID(as_uuid=True), ForeignKey(UploadedFile.file_id, ondelete="CASCADE"), nullable=False)
    # sheet_name = Column(String, nullable=False)
    # number_of_students = Column(Integer,nullable=False)

    # students = relationship(
    #    "Student",
    #    back_populates="classroom",
    #    cascade="all, delete-orphan",
    #    passive_deletes=True
    #)
    # file = relationship("UploadedFile", back_populates="classrooms")

    #  WHAT I WANT TO ADD ARE THE FOLLOWING FIELDS
        # "school_name": "متوسطة مرزقان محمد المدعو معمر (قصر الصباحي)",
        # "term": "الأول",
        # "year": "2020-2021",
        # "level": "أولى  متوسط    1",
        # "subject": "المعلوماتية",
        # "classroom_name": "Sheet-0",
        # "sheet_name": "2100001_1",


    for classroom in classrooms:
        try:
        # Create classroom
            new_classroom = Classroom(
                file_id=file_id,
                school_name=classroom.get("school_name", "Unknown"),
                term=classroom.get("term", "Unknown"),
                year=classroom.get("year", "Unknown"),
                level=classroom.get("level", "Unknown"),
                subject=classroom.get("subject", "Unknown"),
                classroom_name=classroom.get("classroom_name", "Unknown"),
                sheet_name=classroom.get("sheet_name", "Unknown"),
                number_of_students=classroom.get("number_of_students", 0),

            )
            
            db.add(new_classroom)
            db.flush()

            # Add students
            students = classroom.get('students', [])
            for student in students:

                new_student = Student(
                    student_id = student['id'],
                    classroom_id = new_classroom.classroom_id,
                    row = student['row'],
                    last_name = student['last_name'],
                    first_name = student['first_name'],
                    date_birth = student['date_of_birth'],
                    # i want to group evaluation and f assign + final exam + observation in one cluster grades : {field:value, field:value, ....}
                    evaluation = to_float_or_none(student['evaluation']),
                    first_assignment = to_float_or_none(student['first_assignment']),
                    final_exam = to_float_or_none(student['final_exam']),
                    observation = to_float_or_none(student['observation']),
                )
                db.add(new_student)
        except Exception as e:
            logger.error(f"Error processing classroom {classroom.get('sheet_name', 'Unknown')}: {str(e)}")
    
    logger.info(f"Successfully processed {len(classrooms)} classrooms")


@router.delete("/file", summary="deletes the uploaded file",) #response_model=WorkbookParseResponse)
async def delete_file(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to delete the XLS uploaded file.
    """
    object_file = db.query(UploadedFile).filter_by(user_id = current_user).first()
    
    if object_file:
        logger.info(f"Deleting file {object_file.file_id}")

        classrooms = db.query(Classroom).filter_by(file_id=object_file.file_id).all()

        for classroom in classrooms:
            db.query(Student).filter_by(classroom_id=classroom.classroom_id).delete()
            db.delete(classroom)

        db.delete(object_file)

        db.commit()
        logger.info("The file and all related classrooms and students have been deleted")

        return {"message": "The XLS file and all related data have been deleted"}
    raise HTTPException(status_code=404, detail="No file has been found")


@router.get("/file", summary="returns the uploaded file")
async def get_file(db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get the filename if it exists from the data base
    """
    
    try:
        user = db.query(User).filter(User.id == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail= "No existing user"
            )
        if not user.file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail= "No existing file. please upload file first"
            )

        logger.debug(f'User: {user.file}')

        return {
            "message":"success",
            "user_name":user.first_name,
            "user_id":user.id,
            "file_info":{
                "file_id":user.file.file_id,
                "file_name":user.file.file_name
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving file info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving file information"
        )



@router.get('file/download', summary="download the uploaded file")
async def download_file(db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to download the XLS uploaded file.
    """
    file = db.query(UploadedFile).filter_by(user_id = current_user).one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="No file has been found")

    logger.info(f"The file path is {file.storage_path}")
    
    current_path = os.getcwd()
    logger.info(f"the current path {current_path}")
    return FileResponse(path=file.storage_path,
                        filename=os.path.basename(file.storage_path),
                        media_type="application/xls"
                        )
