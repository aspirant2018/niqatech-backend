from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse
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
            data = parse_xls(workbook)
        except Exception as parse_error:
            logger.error(f"Error parsing XLS file: {str(parse_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= f"Error parsing XLS file: {str(parse_error)}"
            )
        
        # Database transaction
        try:
            # Create uploaded file record
            uploaded_file = UploadedFile(
                user_id = current_user,
                file_name = file.filename,
            )
        
            db.add(uploaded_file)
            db.flush() # Get the file_id
            populate_database(db, uploaded_file.file_id, data)    
            db.commit()
            logger.info(f"Successfully processed file: {file.filename} for user: {current_user}")          
        
            return {
                "file_id": str(uploaded_file.file_id),
                "num_classrooms": len(data["classrooms"]),
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

    for classroom in classrooms:
        try:
        # Create classroom
            new_classroom = Classroom(
                file_id=file_id,
                sheet_name=classroom.get("sheet_name", "Unknown"),
                number_of_students=classroom.get("number_of_students", 0)
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


# ===============================
# 📁 Classroom ENDPOINTS
# ===============================
@router.get("/classrooms", summary="returns the list all the user's classrooms")
async def get_all_classrooms(db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to list all the user's classrooms
    """
    file = db.query(UploadedFile).filter(UploadedFile.user_id==current_user).first()
    classrooms = db.query(Classroom).filter(Classroom.file_id==file.file_id).all()
    return classrooms

@router.get("/classrooms/{classroom_id}", summary="returns a specific classroom")
async def get_classroom(classroom_id, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get specific classroom
    """
    file = db.query(UploadedFile).filter(User.id==current_user).first()
    classroom = db.query(Classroom).filter(Classroom.file_id==file.file_id, Classroom.classroom_id == classroom_id ).all()
    return classroom



@router.put("/classrooms/{classroom_id}/grades",summary="bulk update")
async def grade_classroom(classroom_id, grades:BulkGradeUpdate, db: Session = Depends(get_db)):
    """
    Endpoint to update the grades of all the students in a specific classroom
    input:
    {
        classroom_grades: [
            {
                student_id:str,
                new_evaluation:float,
                new_first_assignement:float,
                new_final_exam:float,
                new_observation:str
            },
            {
                ...
            },
        ]
    }
    """
    try:
        grade_updates = {update.student_id: update for update in grades.classroom_grades}
        logger.info(f'grades_updates {grade_updates}')

        students = db.query(Student).filter_by(classroom_id=classroom_id).all()
        if not students:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No students found in this classroom {classroom_id}"
                )
            

        updated_students = []
        for student in students:
            if student.student_id in grade_updates:
                grades_update = grade_updates[student.student_id]

                student.evaluation = grades_update.new_evaluation
                student.first_assignment = grades_update.new_first_assignment
                student.final_exam = grades_update.new_final_exam
                student.observation = grades_update.new_observation
            
            updated_students.append(student)
            logger.info(f'Updated grades for student {student.student_id}')
            
        db.commit()

        return {
            "message": f"Updated grades for {len(updated_students)} students",
            "updated_students": [{"student_id": s.student_id,"last_name":s.last_name, "name": s.first_name} for s in updated_students]
                }
    except Exception as e:
        db.rollback()
        logger.info()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update grades"
        )

# ===============================
# 📁 students ENDPOINTS
# ===============================
@router.get("/classrooms/{classroom_id}/students", summary="returns the list all the students in a specific classroom")
async def get_all_classrooms(classroom_id: int, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to list all in a specific classroom
    """
    file = db.query(UploadedFile).filter(UploadedFile.user_id==current_user).first()
    classroom = db.query(Classroom).filter(Classroom.file_id==file.file_id, Classroom.classroom_id == classroom_id).first()
    students = db.query(Student).filter(Student.classroom_id == classroom.classroom_id).all()
    return students

@router.get("/students/{student_id}", summary="returns a specific student")
async def get_all_classrooms(student_id, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get specific student
    """
    file = db.query(UploadedFile).filter(User.id==current_user).first()
    #logger.info(file.classrooms[0].classroom_id)

    classroom_subquery = db.query(Classroom.classroom_id).filter(
        Classroom.file_id == file.file_id
    )
    student = db.query(Student).filter(
        Student.classroom_id.in_(classroom_subquery),
        Student.student_id == student_id
    ).first()
    return student

# ===============================
# 👤 USER PROFILE ENDPOINTS
# ===============================
@router.get("/profile",summary="return the current user profile")
async def get_current_user_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):

    """ Endpoint to get the current user's profile."""
    
    logger.info(f"Fetching profile for user ID: {current_user}")
    user = db.query(User).filter(User.id == current_user).first()
    if not user:
        logger.error(f"User with ID {current_user} not found.")
        raise HTTPException(status_code=404, detail="User not found")


    payload = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "school_name": user.school_name,
        "academic_level": user.academic_level.value,
        "city": user.city,
        "subject": user.subject
    } 
    return JSONResponse(
        content = payload,
        status_code = status.HTTP_200_OK
    )


# ===============================
# 🔐 AUTHENTICATION ENDPOINTS
# ===============================
@router.post("/logout", summary="signs out current user")
async def signout_user(data, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """ Endpoint to sign out the current user."""
    
    logger.info(f"Signing out user ID: {current_user}")
    logger.info(f"Data received for sign out: {data}")

    # Here you would typically invalidate the user's session or JWT token.
    # Since this is a stateless API, we just return a success message.


    return JSONResponse(
        content={"message": "User signed out successfully"},
        status_code=status.HTTP_200_OK
    )


# ===============================
#  ENDPOINTS
# ===============================
@router.put("/students/{student_id}/grades", summary="Update a student's grade")
async def update_grade(
                student_id:str,
                grades: BulkGradeUpdate,
                db: Session = Depends(get_db),
                current_user=Depends(get_current_user)
                ):
    """ Endpoint to update the student's grade."""

    try:
        logger.info(f"Current user ID: {current_user}")
        logger.info(f"Student id: {student_id}")
        logger.info(f"New student's grades: {grades}")

        user = db.query(User).filter_by(id=current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        file = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).first()
        if not file:
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        student = db.query(Student).filter_by(student_id=student_id).first()

        student.grades = grades.evaluation
        student.first_assignment = grades.first_assignment
        student.final_exam = grades.final_exam
        student.observation = grades.observation

        logger.info(f'{student}')
        

        # Commit the change
        db.commit()
        db.refresh(student)

        return {"message": "Grade updated successfully", "student_id": student_id, "new_grade": grades}
    
    except Exception as e:
        logger.error(f"Error updating grade: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    

