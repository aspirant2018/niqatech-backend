from fastapi import APIRouter
# from models.models import TokenData
from schemas.schemas import TokenData
from fastapi import  HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from jose import jwt
from models.models import User

# logging 
import logging

import os


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__routers/auth.py__")


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "245808035770-5e2rf7c0a5kqcfd6d7q4h9r0car8mttc.apps.googleusercontent.com")
SECRET_KEY = "1234"
ALGORITHM = "HS256"



router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}}
)

# Function to generate a JWT token
def generate_jwt_token(user_id: str):
    """
    Generate a JWT token for the authenticated user.
    This is a placeholder function; implement JWT generation logic here.
    """
    payload = {
        "sub": user_id,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# localhost:8000/auth/google
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

        app_jwt_token = generate_jwt_token(user_id)

    
        # Check if the user is already in your database
        if user_id not in database['users']:

            return {
                "message": "User not found in the database. Please register first.",
                "email": email,
                "is_profile_complete": False,
                "jwt_token": None
                }
        
        # In a real app: check/create user in DB, generate your own JWT

        logger.info(f"App jwt token: {app_jwt_token}")

        logger.info({
            "user": user_id,
            "email": email,
            "name": name,
            "message": "User authenticated successfully",
            "jwt_token": app_jwt_token
            })
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "message": "User authenticated successfully",
            "jwt_token": app_jwt_token,
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid ID token")


