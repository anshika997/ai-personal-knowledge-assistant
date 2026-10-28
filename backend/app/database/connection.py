from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """All database models inherit from this class."""
    pass


_engine = None
_SessionLocal = None


def get_engine():
    """Create the engine one time and reuse it."""
    global _engine, _SessionLocal
    if _engine is None:
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set. Check your .env file.")
        _engine = create_engine(
            settings.sqlalchemy_url,
            pool_pre_ping=True,   # test the connection before using it
            pool_recycle=300,     # Neon can sleep, so refresh old connections
        )
        _SessionLocal = sessionmaker(
            bind=_engine, autoflush=False, expire_on_commit=False
        )
    return _engine


def get_db():
    """FastAPI dependency: gives one DB session per request."""
    try:
        get_engine()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()  # always close the session