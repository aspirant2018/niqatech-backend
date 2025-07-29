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

from dotenv import load_dotenv
import logging
import xlrd
import os
from langchain.chat_models import init_chat_model
    


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

load_dotenv()


# from langchain_core import 
def generate():
    for i in range(5):
        yield f"data: message {i}\n\n"
        
class Query(BaseModel):

    thread_id: str
    message: str

@router.post("/chat/reponse", summary="upload an XLS file")
async def reponse(query: Query):
    """
    Endpoint to chat with an AI assistant (tools: RAGs)
    """


    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY is not set in the environment variables.")
        

    model = init_chat_model(model="gpt-3.5-turbo-0125",model_provider="openai")
    response = model.astream(
        input=query.message,
    )
    logger.info(f"Streaming response for query: {response}")
    if not response:
        logger.error("No response received from the model.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get a response from the AI assistant."
        )
    return StreamingResponse(send_completion_events(response), media_type="text/event-stream")



async def send_completion_events(response):
    async for chunk in response:
        yield f"{chunk.content}|"
