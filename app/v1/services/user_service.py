from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from pydantic import BaseModel , Field, EmailStr

from fastapi.responses import JSONResponse


from app.v1.schemas.schemas import ProfileData
from app.v1.auth.dependencies import get_current_user
from app.v1.utils import parse_xls, to_float_or_none


from app.database.database import get_db
from app.database.models import User
from app.database.models import UploadedFile, User, Classroom, Student

from typing import Optional

from sqlalchemy.orm import Session
import logging
import xlrd
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
import os


logger = logging.getLogger("__services/user_services.py__")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = ['.xls', '.xlsx']


async def save_file(content, path) -> None:
    """ Save uploaded file to the specified path."""
    with open(path, 'wb') as f:
        f .write(content)

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

async def process_uploaded_file(file: UploadFile, user_id:str):
    """ Process the uploaded file """

     # Validate the type of file:
    if not file.filename.endswith('.xls'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .xls files are allowed."
        )
    
    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
            detail=f"File too large or equal to 'zero'. Maximum size is {MAX_FILE_SIZE // {1024*1024}} MB")
    # Parse XLS file
    try:
        parsed_data = parse_xls(content)
    except Exception as e:
        logger.error(f"Error parsing XLS file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing XLS file: {str(e)}"
        )
    # Create file record
    uploaded_file = UploadedFile(
        user_id=user_id,
        file_name=file.filename,
    )
    uploaded_file.storage_path = uploaded_file.generate_storage_path()
    # Save file to disk
    try:
        os.makedirs(os.path.dirname(uploaded_file.storage_path), exist_ok=True)
        with open(uploaded_file.storage_path, 'wb') as f:
            f.write(content)
        logger.info(f"File saved: {uploaded_file.storage_path}")
    except OSError as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file"
        )
    
    return uploaded_file, parsed_data


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

    


class UserService:
    async def compete_profile(self, email,first_name,last_name,school_name,academic_level,city,subject,file,db,current_user):
        # Process file if uploaded
        uploaded_file = None
        parsed_data = {}
        
        if file:
            uploaded_file, parsed_data = await process_uploaded_file(file, current_user)

        user = get_user_by_email(db, email)
        user.first_name = first_name
        user.last_name = last_name
        user.school_name = school_name
        user.academic_level = academic_level.lower()
        user.city = city
        user.subject = subject
        user.profile_complete = True

        if uploaded_file:
            db.add(uploaded_file)
            db.flush() # Get the file_id
            populate_database(db, uploaded_file.file_id, parsed_data)    
        
        db.commit()
        db.refresh(user)
        logger.info(f"User {user.email} profile updated successfully.")

        return user , uploaded_file , parsed_data

