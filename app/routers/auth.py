from fastapi import APIRouter
# from models.models import TokenData
from schemas.schemas import TokenData
from fastapi import  HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

# logging 
import logging
from logging.config import dictConfig
from logging_config import LOGGING_CONFIG


dictConfig(LOGGING_CONFIG) 
logger = logging.getLogger("__routers/auth.py__")


GOOGLE_CLIENT_ID = "245808035770-5e2rf7c0a5kqcfd6d7q4h9r0car8mttc.apps.googleusercontent.com"




router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}}
)

@router.post("/google")
async def google_auth(token_data: TokenData):
    """
    Authenticate user via Google OAuth token.
    """

    logger.info("Google token received from frontend.")

    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(
            token_data.token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Extract user info
        user_id = id_info['sub']
        email   = id_info['email']
        name    = id_info.get('name')

        # Check if the user is already in your database
        # In a real app: check/create user in DB, generate your own JWT
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "message": "User authenticated successfully"
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid ID token")
