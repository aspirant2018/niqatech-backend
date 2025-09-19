'''
defines engine, session, Base
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Lngchain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings

# Qdrant imports
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams  

import os
import dotenv
import logging
from uuid import uuid4


logger = logging.getLogger("__database.py__")
logging.basicConfig(level=logging.INFO)

#DATABASE_URL = "sqlite:///./niqatech.db"
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# PostgreSQL
# engine = create_engine("postgresql://postgres:Rahimmazouz707@db:5432/niqatechdb")
engine = create_engine("postgresql://postgres:Rahimmazouz707@localhost:5432/niqatechdb")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class DocumentIndexer:
    def __init__(self,qdrant_db_path):
        self.db_path = qdrant_db_path
        self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large", api_key=OPENAI_API_KEY)
        self.vector_store = None
        self.client = AsyncQdrantClient(self.db_path)


    async def index_in_qdrantdb(self, content, file_name, doc_type, chunk_size=500):
        try:
            # create document object
            document = Document(
                page_content=content,
                metadata={
                    "source": file_name,
                    "type": doc_type
                    }
                )
            logger.info(f"Indexing document: {file_name} of type {doc_type}")
            
            # split document into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                separators=['\\n\\n', '\\n', ','],
                chunk_size=chunk_size,
                chunk_overlap=200,)

            docs = text_splitter.split_documents([document])
            logger.info(f"Document split into {len(docs)} chunks.")

            # Generate uids for each chunk
            uuids = [f"{str(uuid4())}" for _ in range(len(docs))]
            collection_name = "rag_collection"

            collections = await self.client.get_collections()
            if collection_name in [col.name for col in collections.collections]:
                logger.info(f"Collection {collection_name} already exists.")
            else:
                logger.info(f"Creating collection {collection_name}.")
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
                logger.info(f"Created collection {collection_name}.")

                self.vector_store =  QdrantVectorStore.from_existing_collection(collection_name=collection_name, embedding=self.embedding_function, url=self.db_path)

                await self.vector_store.aadd_documents(documents=docs, ids=uuids)

                logger.info(f"Successfully indexed document in QdrantDB")
                return True
            
            
        except Exception as e:
            print(f"Error during indexing: {e}")
            return
    
    def __str__(self):
        return f"DocumentIndexer connected to Qdrant at {self.db_path}"


test = DocumentIndexer("localhost:6333")

with open("app/Decret_executif_n°_25-54_statut_particulier_des_fonctionnaires_appartenant_aux_corps_specifiques_de_leducation_nationale-47-89.md", "r") as f:
    content = f.read()
