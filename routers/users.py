from fastapi import APIRouter
from fastapi import Depends, status
from fastapi import Depends, HTTPException, status, Request
from jose import jwt , JWTError
from schemas.schemas import ProfileData
import logging



def get_current_user(request: Request):
    """
    Extracts the user ID from the JWT token in the request headers.
    This function is used as a dependency in FastAPI routes to ensure that the user is authenticated
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, "1234", algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise JWTError("User ID not found in token")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))





logger = logging.getLogger("__routers/users.py__")

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}}
)

@router.post("/register",summary="Register a new user")
async def register(data: ProfileData, current_user=Depends(get_current_user)):
    """
    Endpoint to register a new user.
    """

    logger.info("Registration data received from frontend.")
    logger.info(f"Current user ID: {current_user}")
    logger.info(f"Profile data: {data}")

    return {"message": "success"}