from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Path to the .env file in the project root folder.
# This file is: backend/app/core/config.py, so the root is 3 folders up.
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    # Database and AI keys (empty by default, so the app can still start)
    DATABASE_URL: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_FALLBACK_MODEL: str = ""   # optional backup model name

    # Embedding model settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384  # this model gives 384 numbers per text

    # Upload and RAG settings
    MAX_FILE_SIZE_MB: int = 10
    CHUNK_SIZE: int = 800       # characters per chunk
    CHUNK_OVERLAP: int = 150    # characters shared between chunks
    TOP_K: int = 5              # how many chunks to retrieve
    MIN_SIMILARITY: float = 0.25  # chunks below this score are ignored

    # Frontend addresses allowed to call this API
    ALLOWED_ORIGINS: str = "http://localhost:8501"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def sqlalchemy_url(self) -> str:
        """Make the URL work with SQLAlchemy + psycopg2."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    @property
    def origins_list(self) -> list[str]:
        """Turn the comma separated origins into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


# One shared settings object for the whole app
settings = Settings()