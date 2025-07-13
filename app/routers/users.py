from fastapi import APIRouter
# from models.models import  ProfileData
from schemas.schemas import ProfileData
import logging
from logging.config import dictConfig
from config import LOGGING_CONFIG




dictConfig(LOGGING_CONFIG) 
logger = logging.getLogger("__routers/users.py__")


router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}}
)

@router.put("/complete_profile",summary="Complete user profile")
async def complete_profile(data: ProfileData):
    """
    Endpoint to complete user profile.
    """

    logger.info("Completing user profile")
    logger.info(f"Profile data: {data}")

    return {
        "message": "Profile completed successfully",
        "profile_data": data
    }