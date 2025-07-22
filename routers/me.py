from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException, status
import logging
from utils import xls2dict 
import xlrd
from schemas.schemas import WorkbookParseResponse
from auth.dependencies import get_current_user

from database.database import get_db
from database.models import UploadedFile, User
from sqlalchemy.orm import Session



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__routers/me.py__")

router = APIRouter(
    prefix="/me",
    tags=["me"],
    responses={404: {"description": "Not found"}}
)

    

@router.post("/upload_file", summary="upload an XLS file",) #response_model=WorkbookParseResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to upload an XLS file.
    """

    logger.info(f"Current user: {current_user}")
    logger.info("Received request to parse XLS file.")
    logger.info(f"file name is {file.filename}")

    if not file.filename.endswith('.xls'):
        logger.error("Invalid file type. Only .xls files are allowed.")
        raise HTTPException(status_code=400, detail="Invalid file type. Only .xls files are allowed.")

    try:   
        content = await file.read()
        workbook = xlrd.open_workbook(file_contents=content,ignore_workbook_corruption=True, formatting_info=True)
        data = xls2dict(workbook)

        my_uploaded_file = UploadedFile(
            user_id = current_user,
            file_name = "xls-file-"+file.filename,
        )
        existing_file = db.query(UploadedFile).filter_by(user_id=my_uploaded_file.user_id).first()
        
        if not existing_file:
            db.add(my_uploaded_file)
            db.commit()
            db.refresh(my_uploaded_file)  # now file_id is filled
        else:
            return {"message": "The user already has a file in his database", "data": []}
    
        logger.info(f"my uploaded file: {my_uploaded_file}")
        return {"message": "XLS file parsed successfully", "data": data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing XLS file: {str(e)}")
    

@router.delete("/delete_file", summary="delete the upoaded file",) #response_model=WorkbookParseResponse)
async def upload_file(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to delete the XLS uploaded file.
    """

    return {"message": "The XLS file has been deleted by the user"}


@router.get("/get_user_info",summary="Get current user profile")
async def get_current_user_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):

    """ Endpoint to get the current user's profile."""
    
    logger.info(f"Fetching profile for user ID: {current_user}")
    user = db.query(User).filter(User.id == current_user).first()
    if not user:
        logger.error(f"User with ID {current_user} not found.")
        raise HTTPException(status_code=404, detail="User not found")


    payload = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "school_name": user.school_name,
        "academic_level": user.academic_level.value,
        "city": user.city,
        "subject": user.subject
    } 
    return JSONResponse(
        content = payload,
        status_code = status.HTTP_200_OK
    )

@router.get("/get_file", summary="get the uploaded file")
async def get_file(db:Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Endpoint to get the filename if it exists from the data base
    """

    user = db.query(User).filter(User.id == current_user).first()

    logger.info(user.file.file_name)    # Access the uploaded file from the user
    logger.info(user.first_name)        # Access the uploaded file from the user

    return {
        "message":"success",
        "user":user.first_name,
        "data":user.file
        }




    
