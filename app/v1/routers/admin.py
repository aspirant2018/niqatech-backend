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

logger = logging.getLogger("__routers/admin.py__")


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}}
)
@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    """ Endpoint to retrieve all users. Admin access required."""
    try:
        users = db.query(User).all()
        return users
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/students/")
def get_all_students(db: Session = Depends(get_db)):
    """ Endpoint to retrieve all students. Admin access required."""
    try:
        students = db.query(Student).all()
        return students
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
