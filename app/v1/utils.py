'''
This file contains utility functions and classes for the Niqatech backend application.
'''

# App packages
from app.v1.schemas.schemas import  QueryExpantion

# Langchain
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate


from typing import List, Dict


import re
import xlrd
from dotenv import load_dotenv
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("__utils.py__")

load_dotenv()


def parse_xls(content):
    """ Parse the content of an XLS file and extract structured data."""


    workbook = xlrd.open_workbook(file_contents=content, ignore_workbook_corruption=True, formatting_info=True)
    
    data = {"classrooms": []}  # Start with a dictionary containing a list of classrooms

    for i in range(len(workbook.sheets()) - 1):
        # Access the current sheet
        sheet = workbook.sheet_by_index(i)
        sheet_name = sheet.name
        #print(f"Processing sheet: {sheet_name}")
        
        text   = sheet.row_values(4)[0]
        term = re.search(r"الفصل\s+(\S+)", text).group(1)
        year = re.search(r"السنة الدراسية\s*:\s*(\d{4}-\d{4})", text).group(1)
        level = re.search(r"الفوج التربوي\s*:\s*([^\d\n\r]+?\d)", text).group(1).strip()
        subject = re.search(r"مادة\s*:\s*(.+)", text).group(1).strip()

        classroom = {
            "school_name": sheet.row_values(3)[0],
            "term": term,
            "year": year,
            "level": level,
            "subject": subject,
            "classroom_name": f"Sheet-{i}",
            "sheet_name": sheet_name,
            "number_of_students": sheet.nrows - 8,
            "students": []  # Store students in a list
        }

        for row in range(8, sheet.nrows):
            student = {
                "id": int(sheet.row_values(row)[0]),
                "row": row,
                "last_name": sheet.row_values(row)[1],
                "first_name": sheet.row_values(row)[2],
                "date_of_birth": sheet.row_values(row)[3],
                "evaluation": sheet.row_values(row)[4],
                "first_assignment": sheet.row_values(row)[5],
                "final_exam": sheet.row_values(row)[6],
                "observation": sheet.row_values(row)[7]
            }
            classroom["students"].append(student)

        data["classrooms"].append(classroom)  # Add classroom to the list

    return data  # Return the dictionary


def to_float_or_none(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
    
def parse_file():
    pass



async def expand_query(query: str) -> List[str]:
    """
    Expand the given query into a list of similar queries using a language model.
    """
    
    query_template = (
    "You are a search query expansion expert. Your task is to expand and improve the given query "
    "to make it more detailed and comprehensive. Include relevant synonyms and related terms to improve retrieval. "
    "Return only the expanded query without any explanations or additional text."
    "Provide 4 different expanded queries in a list format."
    )

    query_expansion_model = init_chat_model(model="gpt-4.1",
                                            model_provider="openai"
                                            ).with_structured_output(QueryExpantion)

    prompt_template = ChatPromptTemplate([
        ("system", query_template),
        ("human", f"{query}"),
    ])

    messages = prompt_template.invoke({"query": query})
    queries = await query_expansion_model.ainvoke(messages)

    queries = list(queries.queries)
    logger.info(f"Queries after expantion:\n {queries}")

    if isinstance(queries, list):
        queries.append(query)
    else:
        logger.warning("The output of the query expansion model is not a list. Using the original query only.")
        queries = [query]
    
    return queries

from qdrant_client.http.models import SearchRequest


async def retrieve_from_qdrant(embedding_queries, collection_name, client):
    """
    Retrieve documents from Qdrant based on the provided embedding queries.
    """
    scored_points = await client.search_batch(
      collection_name=collection_name,
      requests=[SearchRequest(vector=vector, limit=2) for vector in embedding_queries],
   )
    
    logger.info(f"Results type: {type(scored_points)}")
    logger.info(f"Number of results: {len(scored_points)}")
    
    scored_points = [item for sublist in scored_points for item in sublist]  # Flatten the list of lists
    logger.info(f"Number of scored points after flattening: {len(scored_points)}")

    # Get content from ids 
    ids = [score_point.id for score_point in scored_points]
    logger.info(f"Number of unique ids: {len(ids)}")

    results = await client.retrieve(
        collection_name=collection_name,
        ids=ids,
        )

    return results


from passlib.context import CryptContext

#PIPPER = "mysecretpepper"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password:str):
    """ Hash a plaintext password using bcrypt."""

    peppred_password = password 

    return pwd_context.hash(peppred_password)

def verify_password(plain_password, hashed_password):
    """ Verify a plaintext password against a hashed password."""
    
    peppred_password = plain_password

    return pwd_context.verify(peppred_password, hashed_password)

