import logging

from sqlalchemy import text

from app import models  # noqa: F401  (this import registers all tables)
from app.core.logging_config import setup_logging
from app.database.connection import Base, get_engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    engine = get_engine()

    # Step 1: enable the pgvector extension
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Step 2: create all tables that do not exist yet
    Base.metadata.create_all(bind=engine)
    logger.info("Database is ready (pgvector enabled, tables created).")


if __name__ == "__main__":
    setup_logging()
    init_db()
    print("Database initialized successfully.")