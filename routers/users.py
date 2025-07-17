from fastapi import APIRouter, HTTPException
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from schemas.schemas import ProfileData
from database.database import User, get_db
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
import logging


logger = logging.getLogger("__routers/users.py__")

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)


# create/register a user
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
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        logger.error(f"Error while registering user: {e}")
        db.rollback() # Undo the insert Use it when db.commit() fails or an exception happens.
        raise HTTPException(status_code=500, detail="Internal server error")

    return JSONResponse(
        content={"message": "User registered successfully"},
        status_code=status.HTTP_201_CREATED
    )

@router.get("/me",summary="Get current user profile")
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
    }    # Since this is a stateless API, we just return a success message.


    return JSONResponse(
        content = payload,
        status_code = status.HTTP_200_OK
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