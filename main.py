# FastAPI: the web framework.
# HTTPException: for returning errors to the client.
# BaseModel: for validating request bodies (Pydantic).
# id_token and grequests: from Google's Python SDK, to verify tokens.
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn
import logging
from routers import auth, users, status, student_grades_router



logger = logging.getLogger("__main.py__")


app = FastAPI(
    title = "Niqatech API",
    version = "1.0.0",
    )


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
app.include_router(student_grades_router.router)



if __name__ == "__main__":
    logger.info("Starting FastAPI application")
    uvicorn.run(
        app='main:app',
        host='localhost',
        port=8000,
        reload=True,
        log_level='info'
        )