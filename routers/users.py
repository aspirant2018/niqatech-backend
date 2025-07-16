from fastapi import APIRouter
from fastapi import Depends, status
from fastapi import Depends, HTTPException, status, Request
from jose import jwt , JWTError
from schemas.schemas import ProfileData
import logging
from database.database import User, get_db
from sqlalchemy.orm import Session



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
async def register(data: ProfileData,db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """ Endpoint to register a new user."""

    logger.info("Registration data received from frontend.")
    logger.info(f"Current user ID: {current_user}")
    logger.info(f"Profile data: {data}")
    #  an example of data we would receive from the frontend
    # data = {:
        # email='mazouzceminfo@gmail.com'
        # first_name='Abderahim'
        # last_name='Mazouz'
        # school_name='Merzkan Mohamed'
        # academic_level='Secondry school'
        # city='ksar sbihi'
        # subject='informatique'
        # }

    # id = Column(Integer, primary_key=True)
    # email = Column(String, unique=True, nullable=False)
    # first_name = Column(String, nullable=False)
    # last_name = Column(String, nullable=False)
    # school_name = Column(String, nullable=False)
    # academic_level = Column(Enum(AcademicLevelEnum), nullable=False)
    # city = Column(String, nullable=False)
    # subject = Column(String, nullable=False)
    

    new_user = User(
        id=current_user,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        school_name=data.school_name,
        academic_level=data.academic_level.lower(),
        city=data.city,
        subject=data.subject
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Here we Insert the user into the database


    return {"message": "success"}