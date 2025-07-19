from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException
import logging
from pydantic import BaseModel
from utils import xls2dict 
import xlrd

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

    

@router.post("/upload_file", summary="Parse XLS file", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to parse an XLS file and return classroom data.
    """
    logger.info("Received request to parse XLS file.")
    if not file.filename.endswith('.xls'):
        logger.error("Invalid file type. Only .xls files are allowed.")
        raise HTTPException(status_code=400, detail="Invalid file type. Only .xls files are allowed.")

    try:
        content = await file.read()
        workbook = xlrd.open_workbook(file_contents=content,ignore_workbook_corruption=True, formatting_info=True)
        data = xls2dict(workbook)
        return {"message": "XLS file parsed successfully", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing XLS file: {str(e)}")
