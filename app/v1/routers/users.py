from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse


from app.v1.schemas.schemas import ProfileData
from app.database.database import get_db
from app.database.models import User
from app.v1.auth.dependencies import get_current_user


from sqlalchemy.orm import Session
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