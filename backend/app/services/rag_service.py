import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document, DocumentChunk
from app.services.ai_service import generate_text
from app.services.embedding_service import embed_query

logger = logging.getLogger(__name__)

NOT_FOUND_TOKEN = "NOT_FOUND"
NOT_FOUND_MESSAGE = (
    "I could not find this information in your uploaded documents, "
    "so I will not guess. Try rephrasing the question or upload a relevant document."
)

SYSTEM_PROMPT = (
    "You are a personal knowledge assistant. "
    "Answer the question using ONLY the context given by the user. "
    "Do not use outside knowledge and do not invent facts. "
    "The earlier conversation is only there to help you understand follow-up "
    "questions. Facts must come from the context. "
    f"If the context does not contain the answer, reply with exactly: {NOT_FOUND_TOKEN}"
)

HISTORY_LIMIT = 6   # how many past messages to remember


class SessionNotFoundError(Exception):
    """Raised when the chat session id does not exist."""


def retrieve_chunks(
    db: Session,
    question_vector: list[float],
    top_k: int,
    document_id: Optional[int] = None,
) -> list[dict]:
    """Find the chunks most similar to the question."""
    # cosine_distance: 0 = same meaning, 2 = opposite meaning
    distance = DocumentChunk.embedding.cosine_distance(question_vector).label("distance")

    statement = (
        select(DocumentChunk, Document.filename, distance)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.status == "ready")
    )
    if document_id is not None:
        statement = statement.where(DocumentChunk.document_id == document_id)

    statement = statement.order_by(distance).limit(top_k)

    results = []
    for chunk, filename, dist in db.execute(statement).all():
        results.append(
            {
                "document_id": chunk.document_id,
                "document_name": filename,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "similarity": round(1 - float(dist), 4),  # higher = better match
            }
        )
    return results


def build_prompt(question: str, chunks: list[dict], history: list[ChatMessage]) -> str:
    """Put the chunks, the recent chat and the question into one prompt."""
    blocks = []
    for number, chunk in enumerate(chunks, start=1):
        page = f", page {chunk['page_number']}" if chunk["page_number"] else ""
        blocks.append(f"[Source {number}: {chunk['document_name']}{page}]\n{chunk['content']}")
    context = "\n\n".join(blocks)

    conversation = ""
    if history:
        lines = []
        for message in history:
            who = "User" if message.role == "user" else "Assistant"
            lines.append(f"{who}: {message.content[:500]}")
        conversation = "Earlier conversation:\n" + "\n".join(lines) + "\n\n"

    return f"Context:\n{context}\n\n{conversation}Question: {question}\n\nAnswer:"


def _get_or_create_session(
    db: Session, session_id: Optional[int], question: str
) -> ChatSession:
    if session_id is not None:
        session = db.get(ChatSession, session_id)
        if session is None:
            raise SessionNotFoundError(f"Chat session {session_id} does not exist.")
        return session

    session = ChatSession(title=question[:60])
    db.add(session)
    db.flush()   # gives the new session an id without committing yet
    return session


def _load_history(db: Session, session_id: int) -> list[ChatMessage]:
    """Get the last few messages of this chat, oldest first."""
    rows = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .limit(HISTORY_LIMIT)
        )
        .scalars()
        .all()
    )
    return list(reversed(rows))


def ask_question(
    db: Session,
    question: str,
    session_id: Optional[int] = None,
    top_k: Optional[int] = None,
    document_id: Optional[int] = None,
) -> dict:
    """Full RAG pipeline. Returns a dict that matches AskResponse."""
    session = _get_or_create_session(db, session_id, question)
    history = _load_history(db, session.id)

    # For a follow-up, join the last user question so retrieval keeps the topic
    search_text = question
    last_user_question = next(
        (m.content for m in reversed(history) if m.role == "user"), None
    )
    if last_user_question:
        search_text = f"{last_user_question} {question}"

    # 1) text -> vector, 2) retrieve similar chunks
    question_vector = embed_query(search_text)
    found = retrieve_chunks(db, question_vector, top_k or settings.TOP_K, document_id)

    # 3) keep only chunks that are similar enough
    relevant = [c for c in found if c["similarity"] >= settings.MIN_SIMILARITY]

    answer = NOT_FOUND_MESSAGE
    is_grounded = False
    sources: list[dict] = []

    if relevant:
        # 4) ask Gemini using only the retrieved context
        raw_answer = generate_text(
            build_prompt(question, relevant, history), SYSTEM_PROMPT
        )

        if NOT_FOUND_TOKEN not in raw_answer:
            answer = raw_answer
            is_grounded = True
            sources = [
                {
                    "document_id": c["document_id"],
                    "document_name": c["document_name"],
                    "page_number": c["page_number"],
                    "similarity": c["similarity"],
                    "snippet": c["content"][:300],
                }
                for c in relevant
            ]

    # 5) save both messages in the chat history
    db.add(ChatMessage(session_id=session.id, role="user", content=question))
    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
            sources=sources,
            is_grounded=is_grounded,
        )
    )
    db.commit()

    return {
        "answer": answer,
        "answer_type": "document_grounded" if is_grounded else "not_found_in_documents",
        "is_grounded": is_grounded,
        "sources": sources,
        "session_id": session.id,
    }


def delete_session(db: Session, session_id: int) -> None:
    """Delete a chat session and all its messages."""
    session = db.get(ChatSession, session_id)
    if session is None:
        raise SessionNotFoundError(f"Chat session {session_id} does not exist.")
    db.delete(session)
    db.commit()