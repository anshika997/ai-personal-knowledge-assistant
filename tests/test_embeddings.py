import pytest

from app.services.embedding_service import embed_texts


@pytest.mark.slow
def test_embeddings_have_384_numbers_and_capture_meaning():
    vectors = embed_texts(
        [
            "The cat sits on the mat",
            "A kitten rests on a rug",
            "Stock markets fell sharply today",
        ]
    )
    assert all(len(vector) == 384 for vector in vectors)

    def similarity(a, b):
        # Vectors are normalized, so the dot product is the cosine similarity
        return sum(x * y for x, y in zip(a, b))

    assert similarity(vectors[0], vectors[1]) > similarity(vectors[0], vectors[2])