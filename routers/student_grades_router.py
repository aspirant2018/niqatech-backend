from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException
import logging
from utils import xls2dict 
import xlrd
from schemas.schemas import WorkbookParseResponse
from database.database import UploadedFile, get_db
from sqlalchemy.orm import Session



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__routers/student_grades_router.py__")

router = APIRouter(
    prefix="/classrooms",
    tags=["classrooms"],
    responses={404: {"description": "Not found"}}
)

    

@router.post("/upload_file", summary="Parse XLS file", response_model=WorkbookParseResponse)
async def upload_file(file: UploadFile = File(...), user: str = Form(...), db: Session = Depends(get_db)):
                      # db: Session = Depends(get_db),
                      # current_user=Depends(get_current_user)
    """
    Endpoint to parse an XLS file and return classroom data.
    """

    logger.info(f"User: {user}")
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
            user_id = user,
            file_name = file.filename,
        )

        db.add(my_uploaded_file)
        db.commit()
        db.refresh(my_uploaded_file)  # now file_id is filled

        logger.info(f"my uploaded file: {my_uploaded_file}")


        return {"message": "XLS file parsed successfully", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing XLS file: {str(e)}")
