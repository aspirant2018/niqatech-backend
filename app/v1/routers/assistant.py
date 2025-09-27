# Fastapi 
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse

# App packages
from app.v1.utils import parse_xls, to_float_or_none
from app.v1.schemas.schemas import WorkbookParseResponse, FileUploadResponse
from app.v1.auth.dependencies import get_current_user
from app.database.database import get_db, DocumentIndexer
from app.database.models import UploadedFile, User, Classroom, Student

# Sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from pydantic import BaseModel

# Langchain
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

#from langchain_docling import DoclingLoader
#from langchain_docling.export_type import ExportType
from typing import List, Dict



# Qdrant packages
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models.models import SearchRequest

from dotenv import load_dotenv
from pathlib import Path
import logging
import os
import getpass
import re




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

from pydantic import BaseModel, Field
class QueryExpantion(BaseModel):
    """Always use this tool to structure your response to the user."""
    queries: list[str] = Field(description="list of 4 of similair queries used for retrieval of documents")

        
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
    
    logger.info(f"The query: {query.query}")

    query_template = """
    You are a search query expansion expert. Your task is to expand and improve the given query
    to make it more detailed and comprehensive. Include relevant synonyms and related terms to improve retrieval.
    Return only the expanded query without any explanations or additional text.
    Provide 5 different expanded queries in a list format.
    """

    # Query Expantion:
    query_expansion_model = init_chat_model(model="gpt-4.1",model_provider="openai").with_structured_output(QueryExpantion)

    prompt_template = ChatPromptTemplate([
        ("system", query_template),
        ("human", f"{query}"),
    ])

    messages = prompt_template.invoke({"query": query.query})
    queries = await query_expansion_model.ainvoke(messages)

    queries = list(queries.queries)
    logger.info(f"Queries after expantion:\n {queries}")

    if isinstance(queries, list):
        queries.append(query.query)
    else:
        logger.warning("The output of the query expansion model is not a list. Using the original query only.")
        queries = [query.query]


    # Retrieval
    model = init_chat_model(model="gpt-4.1", model_provider="openai")


    # Generate similaire queries
    client = AsyncQdrantClient(url="http://qdrant:6333")

    collection_name = "rag_collection"
    if not await client.collection_exists(collection_name=collection_name):
        response = model.astream(
        input=query.query,
        )
        return StreamingResponse(send_completion_events(response), media_type="text/event-stream")

        #raise HTTPException(
        #    status_code=status.HTTP_404_NOT_FOUND,
        #    detail=f"'{collection_name}' Not Found"
        #) 
    

    embedding_model = OpenAIEmbeddings(model="text-embedding-3-large",
                                          api_key=os.environ.get("OPENAI_API_KEY")
                                          )

    embedding_queries = embedding_model.embed_documents(queries)
    logger.info(f"The number of vectors: {len(embedding_queries), len(embedding_queries[0])}")
    logger.info(f"Show vector: {embedding_queries[0][0:5]} ... {embedding_queries[0][-5:]}")


    scored_points = await client.search_batch(
      collection_name=collection_name,
      requests=[SearchRequest(vector=vector, limit=2) for vector in embedding_queries],
   )
    logger.info(f"Results type: {type(scored_points)}")
    logger.info(f"Number of results: {len(scored_points)}")
    #logger.info(f"Show results: {results}")
    
    scored_points = [item for sublist in scored_points for item in sublist]  # Flatten the list of lists
    logger.info(f"Number of scored points after flattening: {len(scored_points)}")



    # gGet content from ids 

    ids = [score_point.id for score_point in scored_points]
    logger.info(f"Number of unique ids: {len(ids)}")

    results = await client.retrieve(
        collection_name=collection_name,
        ids=ids,
        )

    # Re-ranking
    
    # Context creation
    context = "\n".join([f"{res.payload.get("page_content", None)}" for res in results])
    logger.info(f"Context:\n{context}")

    # Generation
    system_prompt = """
    You are an assistant for question-answering tasks. you must be polite and helpful
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    """
    prompt_template = ChatPromptTemplate([
        ("system", system_prompt),
        ("human", f"Question: {query}"),
        ("human", f"Context':\n{context}")
    ])

    messages = prompt_template.invoke({"query": query.query, "context":context})
    logger.info("Final messages to the model: {messages}")

    response = model.astream(
        input=messages,
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

    my_document_indexer = DocumentIndexer("http://qdrant:6333")
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
