from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from app.v1.utils import parse_xls, to_float_or_none

from app.v1.schemas.schemas import WorkbookParseResponse, FileUploadResponse
from app.v1.auth.dependencies import get_current_user
from app.database.database import get_db, DocumentIndexer
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


# from langchain_openai import OpenAIEmbeddings

# embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# from langchain_core import 
#def generate():
#    for i in range(5):
#        yield f"data: message {i}\n\n"
# import chromadb
# from langchain_chroma import Chroma


# client = chromadb.PersistentClient(path="./chroma_langchain_db")

# collection = client.get_or_create_collection("laws_collection")
        
class Query(BaseModel):
    query: str

async def send_completion_events(response):
    async for chunk in response:
        yield f"{chunk.content}"


@router.post("/chat/reponse", summary="chat with the AI assistant")
async def reponse(query: Query, db: Session = Depends(get_db)):
    """
    Endpoint to chat with an AI assistant (tools: RAGs)
    """
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY is not set in the environment variables.")

    
    from qdrant_client import QdrantClient, AsyncQdrantClient

    client = AsyncQdrantClient(url="http://localhost:6333")

    collection_name = "rag_collection"
    if not await client.collection_exists(collection_name=collection_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{collection_name}' Not Found"
        ) 

        
    logger.info(f"Streaming response for query: {query.query}")
    # Langchain chatmodel wrapper 
    model = init_chat_model(model="gpt-3.5-turbo-0125",model_provider="openai")

    from langchain_openai import OpenAIEmbeddings

    embedding_function = OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.environ.get("OPENAI_API_KEY"))

    single_vector = embedding_function.embed_query(query.query)
    logger.info(f"The first 100 characters of the vector: {str(single_vector)[:100]}")


    results = await client.search(
      collection_name=collection_name,
      query_vector=single_vector,  # type: ignore
      limit=10,
   )

   
    # logger.info(f" Found documents: {results}")

    #for res in results:
    #    print(res.payload.get("page_content",None))

    context = "\n".join([f"{res.payload.get("page_content",None)}" for res in results])

    user_message = f"""
    Only use this Context:\n{context}\n\n to answer the user's query: {query.query}
    """

    response = model.astream(
        input=user_message,
    )
    
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

    content  = await file.read()

    my_document_indexer = DocumentIndexer("localhost:6333")
    logger.info(f"document indexer: {my_document_indexer}")


    if not my_document_indexer.vector_store:

        logger.info(f"vectore store does'nt exist")
        await my_document_indexer.index_in_qdrantdb(
            content=content,
            file_name="test",
            doc_type="md",
            chunk_size=200
        )


        return JSONResponse(content='File processed and stored successfully',status_code=200)









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
