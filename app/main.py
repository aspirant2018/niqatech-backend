# FastAPI: the web framework.
# HTTPException: for returning errors to the client.
# BaseModel: for validating request bodies (Pydantic).
# id_token and grequests: from Google's Python SDK, to verify tokens.
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn

# logging 
import logging
from logging.config import dictConfig
from logging_config import LOGGING_CONFIG

from routers import auth, users, status



dictConfig(LOGGING_CONFIG) 
logger = logging.getLogger("__main.py__")


app = FastAPI()


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



if __name__ == "__main__":
    logger.info("Starting FastAPI application")
    uvicorn.run(
        app='main:app',
        host='localhost',
        port=8000,
        reload=True,
        log_level='info'
        )