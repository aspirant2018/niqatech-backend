from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__dependencies.py__")


def get_current_user(request: Request):
    """
    Extracts the user ID from the JWT token in the request headers.
    This function is used as a dependency in FastAPI routes to ensure that the user is authorized.
    """
     # logger.info(f"Headers: {request.headers}")
    logger.info(f"Authorization Header: {request.headers.get('Authorization')}")

    
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
        logger.info(f"Payload! {payload}")
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise JWTError("User ID not found in token")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


