# FastAPI: the web framework.
# HTTPException: for returning errors to the client.
# BaseModel: for validating request bodies (Pydantic).
# id_token and grequests: from Google's Python SDK, to verify tokens.
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import uvicorn

# logging 
import logging
from logging.config import dictConfig
from logging_config import LOGGING_CONFIG







dictConfig(LOGGING_CONFIG) 
logger = logging.getLogger("__main.py__")


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Replace with your actual Google client ID
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"

class TokenData(BaseModel):
    id_token: str


@app.get("/")
async def index():
    return {"message": "Welcome to the FastAPI Google Auth Example"}


@app.post("/api/auth/google")
async def google_auth(token_data: TokenData):
    logger.info("Received token for authentication")
    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(
            token_data.id_token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Extract user info
        user_id = id_info['sub']
        email   = id_info['email']
        name    = id_info.get('name')

        # In a real app: check/create user in DB, generate your own JWT
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "message": "User authenticated successfully"
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid ID token")
    

if __name__ == "__main__":
    logger.info("Starting FastAPI application")
    uvicorn.run(
        app='main:app',
        host='localhost',
        port=8000,
        reload=True,
        log_level='info'
        )