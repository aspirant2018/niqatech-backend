from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from pydantic import BaseModel , Field, EmailStr

from fastapi.responses import JSONResponse


from app.v1.schemas.schemas import ProfileData
from app.database.database import get_db
from app.database.models import User
from app.v1.auth.dependencies import get_current_user
from typing import Optional

from sqlalchemy.orm import Session
import logging
from app.v1.utils import parse_xls, to_float_or_none
import xlrd
from app.database.models import UploadedFile, User, Classroom, Student
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel



logger = logging.getLogger("__routers/users.py__")



router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

# Consonants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = ['.xls', '.xlsx']



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

# create/register a user
@router.post("/register",summary="Register a new user")
async def register(
                    email: EmailStr = Form(...),
                    first_name: str = Form(...),
                    last_name: str = Form(...),
                    school_name: str = Form(...),
                    academic_level: str = Form(...),
                    city: str = Form(...),
                    subject: str = Form(...),
                    file: Optional[UploadFile] = File(None),
                    db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)
                    ):
    """ Endpoint to register a new user."""

    logger.info("Registration data received from frontend.")
    logger.info(f"Current user ID: {current_user}")
    # check if the user already exists
    logger.info(f"Email: {email}, First Name: {first_name}, Last Name: {last_name}, "
                f"School Name: {school_name}, Academic Level: {academic_level}, "
                f"City: {city}, Subject: {subject}")
    
    # check if a file is uploaded
    if file:
        logger.info(f"File uploaded: {file.filename}")
        # Check file extension
        if not file.filename.endswith('.xls'):
            logger.error("Invalid file type. Only .xls files are allowed.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only .xls files are allowed."
                )
        # Here you would typically parse the file and extract data.
        # parse the file

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

            try:    
                workbook = xlrd.open_workbook(file_contents=content, ignore_workbook_corruption=True, formatting_info=True)
                data = parse_xls(workbook)
            except Exception as parse_error:
                logger.error(f"Error parsing XLS file: {str(parse_error)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail= f"Error parsing XLS file: {str(parse_error)}"
                )

            # Create uploaded file record
            uploaded_file = UploadedFile(
                user_id = current_user,
                file_name = file.filename,
            )
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading file: {str(e)}"
            )
    else:
        logger.info("No file uploaded, proceeding with user registration without file data.")
        data = {}


    new_user = User(
        id=current_user,
        email=email,
        first_name=first_name,
        last_name=last_name,
        school_name=school_name,
        academic_level=academic_level.lower(),
        city=city,
        subject=subject
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception as e:
        logger.error(f"Error while registering user: {e}")
        db.rollback() # Undo the insert Use it when db.commit() fails or an exception happens.
        raise HTTPException(status_code=500, detail="Internal server error")
    
    if file:
        # Database transaction
        try:
            db.add(uploaded_file)
            db.flush() # Get the file_id
            populate_database(db, uploaded_file.file_id, data)    
            db.commit()
            logger.info(f"Successfully processed file: {file.filename} for user: {current_user}")      
        except SQLAlchemyError as e:
            logger.error(f"Database error while processing file: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,)

    return JSONResponse(
        content={
                    "message": "User registered successfully",
                    "data": data,
                },
        status_code=status.HTTP_201_CREATED
    )



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
        