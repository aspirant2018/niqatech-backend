from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from app.v1.auth.jwt_utils import generate_jwt_token

from app.database.models import User
from app.database.database import get_db
from app.v1.schemas.schemas import TokenData, ItemResponse, LoginResponse
from fastapi import status
from fastapi.responses import JSONResponse


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
    tags=["Auth"],
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
        id_info = id_token.verify_oauth2_token(
            token_data.token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )

        logger.info(f"ID info: {id_info}")

        # Extract user info
        user_id = id_info.get('sub', None)
        email   = id_info.get('email', None)

        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info(f"User ID: {user_id}, Email: {email}")
        
        users = db.query(User).all()
        logger.info(f"Number of users in the database: {len(users)}")

        app_jwt_token = generate_jwt_token(user_id,
                                           SECRET_KEY,
                                           ALGORITHM)
        user = db.query(User).filter(User.id == user_id).first()

        logger.info(f"Users {users}")  # Ensure the database is connected
        logger.info(f"JWT token generated: {app_jwt_token}")
        logger.info(f"The user retrieved from the database: {user}")

        # User is in the database
        if user:
            logger.info(f"User with ID {user_id} found in the database.")
            return JSONResponse(
                status_code=400,
                content={"message": "User already exists"}
            )
            #return {
            #    "message": "User authenticated successfully",
            #    "user_id": user_id,
            #    "email": email,
            #    "first_name": user.first_name,
            #    "last_name": user.last_name,
            #    "is_profile_complete": True,
            #    "jwt_token": app_jwt_token,
            #}

        logger.info(f"User with ID {user_id} not found in the database. Creating a new user.")
        return {
                "message": "User first login. Please complete the profile.",
                "user_id": user_id,
                "email": email,
                "is_profile_complete": False,
                "jwt_token": app_jwt_token
                }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid ID token")



@router.post("/login", response_model=LoginResponse)
async def login(token_data: TokenData, db: Session = Depends(get_db)):
    """
    Login user with JWT token.
    """
    
    logger.info("Login request received.")
    logger.info(f"Token data: {token_data}")

    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(
            token_data.token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )

        logger.info(f"ID info: {id_info}")

        # Extract user info
        user_id = id_info['sub']
        email   = id_info['email']

        logger.info(f"User ID: {user_id}, Email: {email}")
 

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.email == email).one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"User {user.email} logged in successfully.")

        

        return {
            "message": "User logged in successfully",
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "school_name": user.school_name,
            "academic_level": user.academic_level,
            "city": user.city,
            "subject": user.subject,
            "is_profile_complete": True,
            "jwt_token": generate_jwt_token(user_id, SECRET_KEY, ALGORITHM)
        }

    except jwt.JWTError as e:
        logger.error(f"JWT error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
