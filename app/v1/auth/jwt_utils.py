from jose import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY")  # Use a secure key in production
ALGORITHM = os.getenv("ALGORITHM")  # Use a secure algorithm


# Function to generate a JWT token
async def create_access_token(data):
    """
    Generate a JWT token for the authenticated user.
    This is a placeholder function; implement JWT generation logic here.
    """
    to_enocde = data.copy()
    # add expiration time if needed
    # to_enocde.update({"exp": datetime.utcnow() + timedelta(minutes=15)})

    token = jwt.encode(to_enocde, SECRET_KEY, algorithm=ALGORITHM)
    return token
