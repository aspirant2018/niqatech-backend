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
from pathlib import Path


from dotenv import load_dotenv
import logging
import os
from langchain.chat_models import init_chat_model
#from langchain_docling import DoclingLoader
# #from langchain_docling.export_type import ExportType


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

import getpass
import os


from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# from langchain_core import 
#def generate():
#    for i in range(5):
#        yield f"data: message {i}\n\n"
import chromadb
# from langchain_chroma import Chroma

'''

vector_store = Chroma(
    collection_name="laws_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",
)
'''


client = chromadb.PersistentClient(path="./chroma_langchain_db")

collection = client.get_or_create_collection("laws_collection")
        
class Query(BaseModel):
    query: str

async def send_completion_events(response):
    async for chunk in response:
        yield f"{chunk.content}"


@router.post("/chat/reponse", summary="upload an XLS file")
async def reponse(query: Query):
    """
    Endpoint to chat with an AI assistant (tools: RAGs)
    """
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY is not set in the environment variables.")
        

    model = init_chat_model(model="gpt-3.5-turbo-0125",model_provider="openai")

    results = vector_store.similarity_search_by_vector(
        embedding=embeddings.embed_query(query.query), k=5)    #for res in results:
        #logger.info(f"* {res.page_content} [{res.metadata}]")

    context = "\n".join([f"{res.page_content} [{res.metadata}]" for res in results])

    user_message = f"Context:\n{context}\n\nUser Query: {query.query}"

    response = model.astream(
        input=user_message,
    )
    logger.info(f"Streaming response for query: {context}")
    if not response:
        logger.error("No response received from the model.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get a response from the AI assistant."
        )
    return StreamingResponse(send_completion_events(response), media_type="text/event-stream")

@router.post("/file/upload", summary="upload files")
async def reponse(file: UploadFile = File(...)):
    """
    Endpoint to upload a file into a vectorial database
    This endpoint accepts a file upload, processes it, and stores the content in a vectorial database.
    input:
    - file: UploadFile - The file to be processed and stored.
    output:
    - A JSON response indicating the success of the operation.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
        
    temp_file_path = Path(f"./temp_{file.filename}")
    with open(temp_file_path, "wb") as f:
            f.write(await file.read())

    # TODO
    # Parse the PDF file
    raw_text = parse_file(temp_file_path).lower().strip('\n\n')
    articles = extract_articles_with_chapters(raw_text)


    from uuid import uuid4
    from langchain_core.documents import Document

        

    documents = []
    i = 0
    for article in articles["output"]:
        document = Document(
            page_content=article["content"],
            metadata={
                "source": "temp_Decret_executif_n°_25-54_statut_particulier_des_fonctionnaires_appartenant_aux_corps_specifiques_de_leducation_nationale-47-49.pdf",
                "chapter": article['chapter']['title']
                },
            id=i+1,
        )
        documents.append(document)

    logger.info(f"Document created: {documents}")

    # Add documents to the vector store
    # Generate unique IDs for each document
    uuids = [str(uuid4()) for _ in range(len(documents))]
    vector_store.add_documents(documents=documents, ids=uuids)

    temp_file_path.unlink() # Remove the temporary file after processing
   

    return  {'message': "File processed and stored successfully", "articles": articles["output"]} 





def parse_file(temp_file_path: Path):
    """
    Parse the file and convert it to text format using Docling.
    """
    
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(str(temp_file_path))
    output = result.document.export_to_markdown()

    return output




def split(content):
    pass

def embedding(chunk):
    pass

def store(vector):
    pass
    


import re
from typing import List, Dict


import re

def extract_articles_with_chapters(text):
    # Regex to match chapters like: "chapitre 1er ## title" or "chapitre 2 ## title"
    chapitre_pattern = re.compile(
        r'(chapitre\s+(?:1er|\d+))\s*##\s*(.+)', re.IGNORECASE)

    # Regex to match articles: "article 1er" or "art. {number}"
    article_pattern = re.compile(
        r'\b(article\s+1er|art\.\s*\d+)\b', re.IGNORECASE)

    # Extract all chapter matches with their position
    chapitres = []
    for match in chapitre_pattern.finditer(text):
        chapitres.append({
            "start": match.start(),
            "id": match.group(1).strip().lower(),
            "title": match.group(2).strip()
        })

    # Extract all articles with their position
    articles = list(article_pattern.finditer(text))

    # Build the result list
    results = []
    for idx, art in enumerate(articles):
        start = art.start()
        end = articles[idx + 1].start() if idx + 1 < len(articles) else len(text)

        # Find the closest preceding chapter
        chapitre_meta = None
        for chapitre in reversed(chapitres):
            if chapitre["start"] < start:
                chapitre_meta = {
                    "id": chapitre["id"],
                    "title": chapitre["title"]
                }
                break

        results.append({
            "article": art.group().strip(),
            "chapter": chapitre_meta,
            "content": text[start:end].strip()
        })

    return {"output": results}
