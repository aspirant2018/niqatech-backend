from google.auth.transport import requests as grequests
from database.database import SessionLocal, User
from fastapi import APIRouter, Depends
from schemas.schemas import TokenData
from fastapi import  HTTPException
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from jose import jwt
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
async def google_auth(token_data: TokenData, db: Session = Depends(get_db)):
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
        logger.info(f"JWT token generated: {app_jwt_token}")

        user = db.query(User).filter(User.id == user_id).first()
        logger.info(f"The user retrieved from the database: {user}")

        # Check if the user is already in your database
        if user is None:
            logger.info(f"User with ID {user_id} not found in the database. Creating a new user.")
            return {
                "message": "User first login. Please complete your infomrations.",
                "email": email,
                "is_profile_complete": False,
                "jwt_token": app_jwt_token
                }
        
        logger.info(f"User with ID {user_id} found in the database.")
        
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "message": "User authenticated successfully",
            "jwt_token": app_jwt_token,
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid ID token")


