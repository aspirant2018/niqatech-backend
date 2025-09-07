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


print("=== ME.PY FILE LOADED ===")

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
# 📁 students ENDPOINTS
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
        
        logger.info(f'User found: {user}')
        file = db.query(UploadedFile).filter(UploadedFile.user_id == current_user).first()

        if not file:
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        logger.info(f'File found: {file}')
        
        student = db.query(Student).filter_by(id=student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        logger.info(f'Student found: {student}')

        # class StudentGradeUpdate(BaseModel):
        # id: str = Field(..., description="Database student record ID")
        # student_id: str = Field(..., description="Student ID")
        # new_evaluation:  float = Field(..., ge=0.0, le=20.0, description="The evaluation grade (0-20) ")
        # new_first_assignment: float = Field(..., ge=0.0, le=20.0, description="The first assignment grade (0-20) ")
        # new_final_exam: float = Field(..., ge=0.0, le=20.0, description="The final exam grade (0-20) ")
        # new_observation: str  = Field(description="Teacher observation/notes")


        logger.info(f"grades: {grades.classroom_grades[0].new_evaluation}, {grades.classroom_grades[0].new_first_assignment}, {grades.classroom_grades[0].new_final_exam}, {grades.classroom_grades[0].new_observation}")

        student.grades = grades.classroom_grades[0].new_evaluation
        student.first_assignment = grades.classroom_grades[0].new_first_assignment
        student.final_exam = grades.classroom_grades[0].new_final_exam
        student.observation = grades.classroom_grades[0].new_observation

        logger.info(f'{student}')
        

        # Commit the change
        db.commit()
        db.refresh(student)

        return {"message": "Grade updated successfully", "student_id": student_id, "new_grade": grades}
    
    except Exception as e:
        logger.error(f"Error updating grade: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    

@router.get("/students/{student_id}", summary="returns a specific student")
async def get_all_classrooms(student_id, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get specific student
    """

    logger.info(f"Current user ID: {current_user}")
    logger.info(f"Student id: {student_id}")

    student = db.query(Student).filter(Student.id==student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="No student was found for this user")
    

    logger.info(f"Student found: {student}")

    return student
