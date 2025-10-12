from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from pydantic import EmailStr

from fastapi.responses import JSONResponse


from app.v1.auth.dependencies import get_current_user


from app.database.database import get_db
from typing import Optional

from sqlalchemy.orm import Session
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.v1.services.user_service import UserService


logger = logging.getLogger("__routers/users.py__")



router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

user_service = UserService()    


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
    
    try:
        user, UploadedFile, parsed_data = await user_service.compete_profile(email,
                                                                             first_name,
                                                                             last_name,
                                                                             school_name,
                                                                             academic_level,
                                                                             city,
                                                                             subject,
                                                                             file,
                                                                             db,
                                                                             current_user)
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
                    "user_id": user.id,
                    "file_id": UploadedFile.file_id,
                    "data": parsed_data,
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
        