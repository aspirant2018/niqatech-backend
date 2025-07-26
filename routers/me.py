from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException, status
import logging
from utils import parse_xls, to_float_or_none
import xlrd
from schemas.schemas import WorkbookParseResponse, FileUploadResponse
from auth.dependencies import get_current_user

from database.database import get_db
from database.models import UploadedFile, User, Classroom, Student
from sqlalchemy.orm import Session



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
    Endpoint to upload an XLS file.
    """

    logger.info(f"Current user: {current_user}")
    existing_user = db.query(User).filter_by(id=current_user).first()
    if not existing_user:
        raise HTTPException(status_code=400, detail="User is registred. Please register first") 
    
    logger.info("Received request to parse XLS file.")
    logger.info(f"file name is {file.filename}")

    if not file.filename.endswith('.xls'):
        logger.error("Invalid file type. Only .xls files are allowed.")
        raise HTTPException(status_code=400, detail="Invalid file type. Only .xls files are allowed.")

    try:   
        content = await file.read()
        workbook = xlrd.open_workbook(file_contents=content,ignore_workbook_corruption=True, formatting_info=True)
        data = parse_xls(workbook)

        logger.info(f"data {type(data)}")
        
        uploaded_file = UploadedFile(
            user_id = current_user,
            file_name = file.filename,
        )

        existing_file = db.query(UploadedFile).filter_by(user_id=uploaded_file.user_id).first()

        if existing_file:
            raise HTTPException(status_code=400, detail="The user already has a file in the database")
        
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file) # now file_id is filled

        logger.info(f"uploaded file is proceeded: {uploaded_file}")            
        populate_database(db, uploaded_file.file_id, data)    
        
        return {
                "file_id": str(uploaded_file.file_id),
                "num_classrooms": len(data["classrooms"]),
                }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing XLS file: {str(e)}")

def populate_database(db: Session, file_id:str , data:dict) -> None:
    classrooms: list = data['classrooms']

    for classroom in classrooms:

        sheet_name = classroom["sheet_name"]
        number_of_students = classroom["number_of_students"]

        new_classroom = Classroom(
            file_id=file_id,
            sheet_name=sheet_name,
            number_of_students=number_of_students
        )
        
        db.add(new_classroom)
        db.flush()

        for student in classroom['students']:

            new_student = Student(
                student_id = student['id'],
                classroom_id = new_classroom.classroom_id,
                row = student['row'],
                last_name = student['last_name'],
                first_name = student['first_name'],
                date_birth = student['date_of_birth'],
                evaluation = to_float_or_none(student['evaluation']),
                first_assignment = to_float_or_none(student['first_assignment']),
                final_exam = to_float_or_none(student['final_exam']),
                observation = to_float_or_none(student['observation']),
            )
            db.add(new_student)
    db.commit()

    logger.info(f"{len(classrooms)} classrooms were proceded")


@router.delete("/file", summary="delete the uploaded file",) #response_model=WorkbookParseResponse)
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


@router.get("/file", summary="get the uploaded file")
async def get_file(db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get the filename if it exists from the data base
    """

    user = db.query(User).filter(User.id == current_user).first()

    logger.info(user.file.file_name)    # Access the uploaded file from the user
    logger.info(user.first_name)        # Access the uploaded file from the user

    return {
        "message":"success",
        "user":user.first_name,
        "data":user.file
        }

# ===============================
# 📁 Classroom ENDPOINTS
# ===============================
@router.get("/classrooms", summary="list all the user's classrooms")
async def get_all_classrooms(db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to list all the user's classrooms
    """
    file = db.query(UploadedFile).filter(User.id==current_user).first()
    classrooms = db.query(Classroom).filter(Classroom.file_id==file.file_id).all()
    return classrooms

@router.get("/classrooms/{classroom_id}", summary="Get specific classroom")
async def get_all_classrooms(classroom_id, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get specific classroom
    """
    file = db.query(UploadedFile).filter(User.id==current_user).first()
    classroom = db.query(Classroom).filter(Classroom.file_id==file.file_id, Classroom.classroom_id == classroom_id ).all()
    return classroom

# ===============================
# 📁 students ENDPOINTS
# ===============================
@router.get("/classrooms/{classroom_id}/students", summary="list all the students in a specific classroom")
async def get_all_classrooms(classroom_id: int, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to list all in a specific classroom
    """
    file = db.query(UploadedFile).filter(User.id==current_user).first()
    classroom = db.query(Classroom).filter(Classroom.file_id==file.file_id, Classroom.classroom_id == classroom_id).first()
    students = db.query(Student).filter(Student.classroom_id == classroom.classroom_id).all()
    return students

@router.get("/classrooms/students/{student_id}", summary="Get specific classroom")
async def get_all_classrooms(student_id, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get specific classroom
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
@router.get("/profile",summary="Get current user profile")
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
@router.post("/logout", summary="Sign out current user")
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

    
