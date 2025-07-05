# FastAPI: the web framework.
# HTTPException: for returning errors to the client.
# BaseModel: for validating request bodies (Pydantic).
# id_token and grequests: from Google's Python SDK, to verify tokens.


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

app = FastAPI()

# Replace with your actual Google client ID
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"

class TokenData(BaseModel):
    id_token: str

@app.post("/api/auth/google")
async def google_auth(token_data: TokenData):
    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(
            token_data.id_token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Extract user info
        user_id = id_info['sub']
        email = id_info['email']
        name = id_info.get('name')

        # In a real app: check/create user in DB, generate your own JWT
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "message": "User authenticated successfully"
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid ID token")