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

print("=== STUDENTS.PY FILE LOADED ===")

# Configure logger for this module
logger = logging.getLogger(__name__)

# Ensure the logger level is set (this can also be done globally)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

router = APIRouter(
    prefix="/me",
    tags=["me"],
    responses={404: {"description": "Not found"}}
)


# ===============================
# 📁 students ENDPOINTS
# ===============================
@router.put("/students/{student_id}/grades", summary="Update a student's grade")
async def update_student_grade(
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

    

@router.get("/students/{student_id}", summary="returns a specific student")
async def get_student_by_id(student_id, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get specific student
    """

    logger.info(f"Current user ID: {current_user}")
    logger.info(f"Student id: {student_id}")

    file = db.query(UploadedFile).filter(UploadedFile.user_id==current_user).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    print(f"Type file: {type(file)}")
    print(f"File: {file.classrooms[0].classroom_id}")
    print(f"File: {file.classrooms[0].students[0].student_id}")

    classroom_subquery = db.query(Classroom.classroom_id).filter(
        Classroom.file_id == file.file_id
    )


    student = db.query(Student).filter(
        Student.classroom_id.in_(classroom_subquery),
        Student.student_id == student_id
    ).first()
    return student
