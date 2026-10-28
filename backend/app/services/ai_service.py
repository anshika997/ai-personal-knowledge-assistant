import logging
import time
from typing import Optional

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

# Error codes that are temporary, so trying again can work
RETRY_CODES = {429, 500, 503, 504}
MAX_ATTEMPTS = 3   # tries per model


class AIServiceError(Exception):
    """Raised when the Gemini API cannot give an answer."""


_client = None


def _get_client():
    """Create the Gemini client one time."""
    global _client
    if not settings.GEMINI_API_KEY:
        raise AIServiceError("GEMINI_API_KEY is not set. Check your .env file.")
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    json_mode: bool = False,
) -> str:
    """Send a prompt to Gemini. Retries on busy errors, then tries a backup model."""
    client = _get_client()

    models = [settings.GEMINI_MODEL]
    backup = settings.GEMINI_FALLBACK_MODEL
    if backup and backup != settings.GEMINI_MODEL:
        models.append(backup)

    last_error = None

    for model in models:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        # json_mode asks Gemini to return only JSON
                        response_mime_type="application/json" if json_mode else None,
                    ),
                )
            except Exception as error:
                last_error = error
                code = getattr(error, "code", None)

                if code in RETRY_CODES and attempt < MAX_ATTEMPTS:
                    wait_seconds = 2 ** attempt   # waits 2s, then 4s
                    logger.warning(
                        "Gemini busy (model=%s, code=%s). Retry %s/%s in %ss",
                        model, code, attempt, MAX_ATTEMPTS, wait_seconds,
                    )
                    time.sleep(wait_seconds)
                    continue

                logger.error("Gemini failed (model=%s): %s", model, error)
                break   # give up on this model, try the backup

            text = getattr(response, "text", None)
            if text:
                return text.strip()

            last_error = "The AI returned an empty answer (it may have been blocked)."
            break

    code = getattr(last_error, "code", None)
    if code in RETRY_CODES:
        raise AIServiceError(
            "The AI service is busy right now. Please try again in a minute."
        )
    raise AIServiceError(f"The AI service request failed: {last_error}")