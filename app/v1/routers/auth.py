from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from app.v1.auth.jwt_utils import create_access_token

from app.database.models import User
from app.database.database import get_db
from app.v1.schemas.schemas import TokenData, SignUpResponse, LoginResponse, LocalSignUp
from fastapi import status
from fastapi.responses import JSONResponse

from jose import jwt
import logging
import os
from app.v1.utils import get_password_hash, verify_password 

from pydantic import BaseModel, EmailStr, constr
import secrets
import uuid
from datetime import datetime
import datetime
from datetime import datetime
from sqlalchemy.exc import IntegrityError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__routers/auth.py__")


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")




router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={404: {"description": "Not found"}}
)

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

async def verify_google_token(token: TokenData):
    """ Verify OAuth token with Google."""
    try:
        id_info = id_token.verify_oauth2_token(
            token.token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        user_id = id_info.get('sub', None)
        email = id_info.get('email', None)

        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            'user_id': user_id,
            'email': email,
        }
    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
def create_user(id: str, email: str, password:str | None, auth_provider: str, db: Session):
    
    hash_password = get_password_hash(password) if password else None
    
    try: 
        new_user = User(
            id=id,
            email=email,
            hash_password=hash_password,
            auth_provider=auth_provider
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    except Exception as e:
        db.rollback()
        logger.exception("Error creating user")
        raise HTTPException(status_code=500, detail="Internal server error")   
     
@router.post("/google/signup", response_model=SignUpResponse)
async def signup(token_data: TokenData, db: Session = Depends(get_db)):
    """ Authenticate user via Google OAuth token."""
    logger.info("Google sign-up request received.")

    
    google_user = await verify_google_token(token_data)
    logger.info(f"User ID: {google_user['user_id']}, Email: {google_user['email']}")
    existing_user = get_user_by_email(db, google_user['email'])

    if existing_user:
        logger.warning(f"Signup attempted for existing user: {google_user['email']}")
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists. Please login instead."
            )

    # If user does not exist, prompt to complete profile
    logger.info(f"User with ID {google_user['user_id']} not found in the database.")
    
    try:
        new_user = create_user(id=google_user['user_id'], email=google_user['email'], password=None, auth_provider="google", db=db)
        logger.info(f"New user created with ID {new_user.id} and email {new_user.email}. password: {new_user.hash_password}")
        access_token = await create_access_token(google_user)

        return {
                "message": "User has been created. Please complete the profile.",
                "user_id": google_user['user_id'],
                "email": google_user['email'],
                "is_profile_complete": False,
                "jwt_token": access_token
                }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid ID token")

        #



@router.post("/google/login", response_model=LoginResponse)
async def google_login(token_data: TokenData, db: Session = Depends(get_db)):
    """Login user with JWT token"""
    
    logger.info("Login request received.")
    try:
        google_user = await verify_google_token(token_data)
        user = get_user_by_email(db, google_user['email'])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.is_profile_complete:
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "message": "Profile incomplete. Please complete your profile.",
                    "user_id": user.id,
                    "email": user.email,
                    "is_profile_complete": False,
                    "jwt_token": await create_access_token(google_user)
                }
            )

        logger.info(f"User {user.email} logged in successfully.")

        user.last_login = datetime.now()
        db.commit()

        access_token = await create_access_token(google_user)



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
            "is_profile_complete": user.is_profile_complete,
            "jwt_token": access_token
        }

    except jwt.JWTError as e:
        logger.error(f"JWT error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")





@router.post("/signup", response_model=SignUpResponse)
async def local_signup(data: LocalSignUp, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.email):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"message": "User already exists"}
        )
    new_user = create_user(id=uuid.uuid4().hex, email=data.email, password=data.password, auth_provider="local", db=db)
    access_token = await create_access_token({"user_id": new_user.id, "email": new_user.email})

    # In a real application, send a verification email here
    return {
        "message": "User first login. Please complete the profile.",
        "user_id": new_user.id,
        "email": new_user.email,
        "is_profile_complete": False,
        "jwt_token": access_token
        }

@router.post("/login", response_model=LoginResponse)
async def local_login(data: LocalSignUp, db: Session = Depends(get_db)):
    logger.info("Local login request received.")

    logger.info(f"Login email: {data.email}. login password: {data.password}    ")
    user = get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hash_password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid email or password"}
        )
    if not user.is_profile_complete:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": "Profile incomplete. Please complete your profile."}
        )
    
    logger.info(f"User {user.email} logged in successfully.")
    try:
        user.last_login = datetime.now()
        db.commit()
    except ValueError as e:
        logger.error(f"Error updating last login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    payload = {
            'user_id': user.id,
            'email': user.email,
    }

    access_token = await create_access_token(payload)
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
        "is_profile_complete": user.is_profile_complete,
        "jwt_token": access_token
    }



