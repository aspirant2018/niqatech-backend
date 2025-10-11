# FastAPI: the web framework.
# HTTPException: for returning errors to the client.
# BaseModel: for validating request bodies (Pydantic).
# id_token and grequests: from Google's Python SDK, to verify tokens.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import uvicorn
import logging
from app.v1.routers import (
    auth,
    users,
    status,
    me,
    assistant,
    file,
    classrooms,
    students,
    admin
    )

from contextlib import asynccontextmanager
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

# Qdrant client
qdrant_client = QdrantClient(
    host="localhost",
    port=6333,
    prefer_grpc=True
)

# Define collections and their configs
COLLECTIONS = {
    "document_embeddings": VectorParams(size=384, distance=Distance.DOT),
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup ----
    existing = [c.name for c in qdrant_client.get_collections().collections]
    for name, config in COLLECTIONS.items():
        if name not in existing:
            qdrant_client.recreate_collection(
                collection_name=name,
                vectors_config=config,
            )
            print(f"✅ Created collection {name}")
        else:
            print(f"ℹ️ Collection {name} already exists")
    
    yield  # <-- application runs here

    # ---- Shutdown ----
    print("🔻 Shutting down app...")



logger = logging.getLogger("__main.py__")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Niqatech API with JWT",
        version="1.0.0",
        description="This is a secured API with JWT",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI()
app.openapi = custom_openapi



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(status.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(me.router)
app.include_router(assistant.router)
app.include_router(file.router)
app.include_router(classrooms.router)
app.include_router(students.router)
app.include_router(admin.router)


if __name__ == "__main__":
    logger.info("Starting FastAPI application")
    uvicorn.run(
        app='main:app',
        host='localhost',
        port=8000,
        reload=True,
        log_level='info'
        )