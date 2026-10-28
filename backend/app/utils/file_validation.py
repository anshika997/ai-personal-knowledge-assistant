import hashlib
from pathlib import Path

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def get_extension(filename: str) -> str:
    """Return the file extension in lowercase, like '.pdf'."""
    return Path(filename).suffix.lower()


def validate_upload(filename: str, size_in_bytes: int) -> None:
    """Raise ValueError with a clear message if the file is not allowed."""
    if not filename:
        raise ValueError("The file has no name.")

    extension = get_extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"File type '{extension}' is not supported. Use PDF, TXT or DOCX."
        )

    if size_in_bytes == 0:
        raise ValueError("The file is empty.")

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size_in_bytes > max_bytes:
        raise ValueError(f"File is too large. Maximum size is {settings.MAX_FILE_SIZE_MB} MB.")


def compute_hash(content: bytes) -> str:
    """A fingerprint of the file. Same file = same hash."""
    return hashlib.sha256(content).hexdigest()