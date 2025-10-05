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


logger = logging.getLogger("__routers/users.py__")

async def save_file(content, path) -> None:
    """ Save uploaded file to the specified path."""
    with open(path, 'wb') as f:
        f .write(content)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

# Consonants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = ['.xls', '.xlsx']

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


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

# complete user profile
@router.post("/register",summary="Complete user profile")
async def complete(
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
    """ Endpoint to complete the user profile."""

    logger.info(f"Registration for user {current_user}: {email}.")
    
    logger.info(f"Email: {email}, First Name: {first_name}, Last Name: {last_name}, "
                f"School Name: {school_name}, Academic Level: {academic_level}, "
                f"City: {city}, Subject: {subject}")
    
    # Process file if uploaded
    uploaded_file = None
    parsed_data = {}
    
    if file:
        uploaded_file, parsed_data = await process_uploaded_file(file, current_user)

    try:
        user = get_user_by_email(db, email)
        user.first_name = first_name
        user.last_name = last_name
        user.school_name = school_name
        user.academic_level = academic_level.lower()
        user.city = city
        user.subject = subject
        user.is_profile_complete = True

        if uploaded_file:
            db.add(uploaded_file)
            db.flush() # Get the file_id
            populate_database(db, uploaded_file.file_id, parsed_data)    
    
        db.commit()
        db.refresh(user)
        logger.info(f"User {user.email} profile updated successfully.")

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
            )

    return JSONResponse(
        content={
                    "message": "Profile completed successfully",
                    "data": parsed_data,
                },
        status_code=status.HTTP_201_CREATED
    )
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
        