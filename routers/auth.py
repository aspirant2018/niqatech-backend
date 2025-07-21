from google.auth.transport import requests as grequests
from database.models import User
from database.database import get_db
from fastapi import APIRouter, Depends
from schemas.schemas import TokenData, ItemResponse
from fastapi import  HTTPException
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from auth.jwt_utils import generate_jwt_token

from jose import jwt
import logging
import os


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__routers/auth.py__")


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "245808035770-5e2rf7c0a5kqcfd6d7q4h9r0car8mttc.apps.googleusercontent.com")
SECRET_KEY = os.getenv("SECRET_KEY", "1234")  # Use a secure key in production
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Use a secure algorithm



router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}}
)


# localhost:8000/auth/google
@router.post("/google", response_model=ItemResponse)
async def google_auth(token_data: TokenData, db: Session = Depends(get_db)):
    """
    Authenticate user via Google OAuth token.
    """

    logger.info("Google token received from frontend.")
    logger.info(f"Token data: {token_data}")

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
        
        users = db.query(User).all()
        app_jwt_token = generate_jwt_token(user_id, SECRET_KEY, ALGORITHM)
        user = db.query(User).filter(User.id == user_id).first()

        logger.info(f"Users {users}")  # Ensure the database is connected
        logger.info(f"JWT token generated: {app_jwt_token}")
        logger.info(f"The user retrieved from the database: {user}")

        # Check if the user is already in your database
        if user is None:

            logger.info(f"User with ID {user_id} not found in the database. Creating a new user.")
            reponse = {
                "message": "User first login. Please complete the.",
                "user_id": user_id,
                "email": email,
                "is_profile_complete": False,
                "jwt_token": app_jwt_token
                }
        
            return reponse 
        
        # If user exists, return user info
        logger.info(f"User with ID {user_id} found in the database.")
        return {
            "message": "User authenticated successfully",
            "user_id": user_id,
            "email": email,
            "is_profile_complete": True,
            "jwt_token": app_jwt_token,
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid ID token")


