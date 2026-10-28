from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.note import Note
from app.services.embedding_service import embed_query
from app.services.rag_service import retrieve_chunks


def semantic_search(
    db: Session,
    query: str,
    top_k: int = 5,
    document_id: Optional[int] = None,
    include_notes: bool = True,
) -> list[dict]:
    vector = embed_query(query)
    results: list[dict] = []

    # 1) Search document chunks
    for chunk in retrieve_chunks(db, vector, top_k, document_id):
        if chunk["similarity"] >= settings.MIN_SIMILARITY:
            results.append(
                {
                    "item_type": "document",
                    "item_id": chunk["document_id"],
                    "title": chunk["document_name"],
                    "page_number": chunk["page_number"],
                    "similarity": chunk["similarity"],
                    "content": chunk["content"][:500],
                }
            )

    # 2) Search notes (only when we are not limited to one document)
    if include_notes and document_id is None:
        distance = Note.embedding.cosine_distance(vector).label("distance")
        rows = db.execute(
            select(Note, distance)
            .where(Note.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
        ).all()
        for note, dist in rows:
            similarity = round(1 - float(dist), 4)
            if similarity >= settings.MIN_SIMILARITY:
                results.append(
                    {
                        "item_type": "note",
                        "item_id": note.id,
                        "title": note.title,
                        "page_number": None,
                        "similarity": similarity,
                        "content": note.content[:500],
                    }
                )

    # Best matches first
    results.sort(key=lambda r: r["similarity"], reverse=True)
    return results[:top_k]