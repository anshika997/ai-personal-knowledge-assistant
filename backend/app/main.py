import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.database.init_db import init_db
from app.routes import (
    ai, dashboard, documents, goals, health, notes, profile, quiz, search,
)

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts
    try:
        init_db()
    except Exception as error:
        logger.error("Database setup failed: %s", error)
    yield


app = FastAPI(
    title="AI Personal Knowledge Assistant",
    description="Upload documents and ask questions using RAG.",
    version="0.2.0",
    lifespan=lifespan,
)

# Allow the Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(ai.router)
app.include_router(profile.router)
app.include_router(notes.router)
app.include_router(goals.router)
app.include_router(search.router)
app.include_router(quiz.router)
app.include_router(dashboard.router)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, error: Exception):
    # Log the real error, but show a safe message to the user
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check the server logs."},
    )


@app.get("/", include_in_schema=False)
def root():
    return {"message": "API is running. Open /docs for Swagger UI."}