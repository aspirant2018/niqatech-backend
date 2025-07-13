from fastapi import APIRouter
from models import  ProfileData
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

@router.put("/complete_profile")
async def complete_profile(data: ProfileData):

    logger.info("Completing user profile")
    logger.info(f"Profile data: {data}")

    return {
        "message": "Profile completed successfully",
        "profile_data": data
    }