from fastapi import APIRouter, HTTPException
from fastapi import Depends
from schemas.schemas import ProfileData
from database.database import User, get_db
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
import logging





logger = logging.getLogger("__routers/users.py__")

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}}
)

@router.post("/register",summary="Register a new user")
async def register(data: ProfileData, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """ Endpoint to register a new user."""

    logger.info("Registration data received from frontend.")
    logger.info(f"Current user ID: {current_user}")
    logger.info(f"Profile data: {data}")

    new_user = User(
        id=current_user,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        school_name=data.school_name,
        academic_level=data.academic_level.lower(),
        city=data.city,
        subject=data.subject
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Here we Insert the user into the database


    return {"message": "success"}


@router.get("/me",summary="Get current user profile")
async def get_current_user_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """ Endpoint to get the current user's profile."""
    
    logger.info(f"Fetching profile for user ID: {current_user}")

    user = db.query(User).filter(User.id == current_user).first()
    if not user:
        logger.error(f"User with ID {current_user} not found.")
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "school_name": user.school_name,
        "academic_level": user.academic_level.value,
        "city": user.city,
        "subject": user.subject
    }