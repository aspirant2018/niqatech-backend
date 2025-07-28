from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from app.v1.utils import parse_xls, to_float_or_none

from app.v1.schemas.schemas import WorkbookParseResponse, FileUploadResponse
from app.v1.auth.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import UploadedFile, User, Classroom, Student
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel


import logging
import xlrd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__routers/assistant.py__")

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
    responses={404: {"description": "Not found"}}
)



def generate():
    for i in range(5):
        yield f"data: message {i}\n\n"
        
class Query(BaseModel):
    query:str

@router.post("/chat/reponse", summary="upload an XLS file")
async def reponse(query: Query):
    """
    Endpoint to chat with an AI assistant (tools: RAGs)
    """
    return StreamingResponse(generate(), media_type="text/event-stream")

