import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_model = None


def get_model():
    """Load the model one time and reuse it."""
    global _model
    if _model is None:
        # Imported here (not at the top) so the server starts with little memory.
        # PyTorch is loaded only when the first upload or question happens.
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        size = _model.get_sentence_embedding_dimension()
        if size != settings.EMBEDDING_DIM:
            raise RuntimeError(
                f"Model gives {size} numbers but EMBEDDING_DIM is {settings.EMBEDDING_DIM}."
            )
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert many texts to vectors."""
    vectors = get_model().encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,  # makes cosine similarity work well
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Convert one question to a vector."""
    return embed_texts([text])[0]