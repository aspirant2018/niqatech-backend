from fastapi import Request, HTTPException, status
from jose import jwt, JWTError


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


