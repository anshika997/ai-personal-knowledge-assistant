import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.database.connection import get_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    database_ok = False
    pgvector_ok = False

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            database_ok = True
            row = connection.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).first()
            pgvector_ok = row is not None
    except Exception as error:
        logger.warning("Health check: database problem: %s", error)

    return {
        "status": "ok" if database_ok and pgvector_ok else "degraded",
        "database_connected": database_ok,
        "pgvector_enabled": pgvector_ok,
        "gemini_key_configured": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
    }