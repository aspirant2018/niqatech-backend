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


@router.get("/classrooms/{classroom_id}/students", summary="returns the list all the students in a specific classroom")
async def get_all_classrooms(classroom_id: int, db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to list all in a specific classroom
    """
    file = db.query(UploadedFile).filter(UploadedFile.user_id==current_user).first()
    classroom = db.query(Classroom).filter(Classroom.file_id==file.file_id, Classroom.classroom_id == classroom_id).first()
    students = db.query(Student).filter(Student.classroom_id == classroom.classroom_id).all()
    return students
