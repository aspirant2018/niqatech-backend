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


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")  # Use a secure key in production
ALGORITHM = os.getenv("ALGORITHM")  # Use a secure algorithm



router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={404: {"description": "Not found"}}
)

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


# localhost:8000/auth/google
# called in signin component in frontend

@router.post("/google", response_model=ItemResponse)
async def google_auth(token_data: TokenData, db: Session = Depends(get_db)):
    """ Authenticate user via Google OAuth token."""

    #logger.info(f"Google token received from frontend, The Token: {token_data}")

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
        

        app_jwt_token = generate_jwt_token(user_id, SECRET_KEY, ALGORITHM)
        user = get_user_by_email(db, email)

        # If user does not exist, prompt to complete profile
        # but i want to create the user fist in db then prompt to complete profile
        import secrets
        if not user:
            logger.info(f"User with ID {user_id} not found in the database.")
            # create a new user with minimal info
            new_user = User(
                id=user_id,
                email=email,
                password=secrets.token_urlsafe(16), # Password can be set later via a password reset mechanism
            )             
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            logger.info(f"New user created with ID {new_user.id} and email {new_user.email}. password: {new_user.password}")

            return {
                "message": "User first login. Please complete the profile.",
                "user_id": user_id,
                "email": email,
                "is_profile_complete": False,
                "jwt_token": app_jwt_token
                }
        if user:
            logger.info(f"User with ID {user_id} found in the database.")
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"message": "User already exists"}
            )
        
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
        
        id_info = id_token.verify_oauth2_token(
            token_data.token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )

        logger.info(f"ID info: {id_info}")

        # Extract user info
        user_id, email = id_info['sub'], id_info['email']
        logger.info(f"User ID: {user_id}, Email: {email}")

        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = get_user_by_email(db, email)
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



from pydantic import BaseModel, EmailStr, constr
import secrets
import uuid



class LocalSignUp(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

@router.post("/local/signup")
async def local_signup(data: LocalSignUp, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.email):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"message": "User already exists"}
        )
    
    new_user = User(
        id = uuid.uuid4().hex,
        email=data.email,
        password=data.password,  # In production, hash the password before storing    
    )

    logger.info(f"Creating user with email: {new_user.email}, ID: {new_user.id}, Password: {new_user.password}")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    app_jwt_token = generate_jwt_token(new_user.id, SECRET_KEY, ALGORITHM)

    # In a real application, send a verification email here

    return {
        "message": "User first login. Please complete the profile.",
        "user_id": new_user.id,
        "email": new_user.email,
        "is_profile_complete": False,
        "jwt_token": app_jwt_token
        }

@router.post("/local/login", response_model=LoginResponse)
async def local_login(data: LocalSignUp, db: Session = Depends(get_db)):
    logger.info("Local login request received.")
    logger.info(f"Login email: {data.email}")
    logger.info(f"Login password: {data.password}")

    user = get_user_by_email(db, data.email)
    if not user or user.password != data.password:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid email or password"}
        )
    
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
        "jwt_token": generate_jwt_token(user.id, SECRET_KEY, ALGORITHM)
    }



