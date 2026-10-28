import json
import logging
import re
from typing import Optional

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.goal import Goal
from app.models.note import Note
from app.models.profile import Profile
from app.schemas.ai import QuizQuestion
from app.services.ai_service import AIServiceError, generate_text
from app.services.embedding_service import embed_query
from app.services.rag_service import retrieve_chunks

logger = logging.getLogger(__name__)

MAX_SUMMARY_CHARS = 40000   # longer text is cut
MAX_QUIZ_CHARS = 15000


class NotFoundError(Exception):
    """Raised when a document does not exist."""


SUMMARY_RULES = {
    "short": "Write a short summary in 3 to 5 sentences.",
    "detailed": "Write a detailed summary in clear paragraphs that covers all main ideas.",
    "key_points": "List the key points as short bullet points. Start each line with '- '.",
}


def _get_ready_document(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError("Document not found.")
    if document.status != "ready":
        raise ValueError("This document is not ready yet or failed processing.")
    return document


# ---------------- Summarizer ----------------
def summarize_content(
    db: Session, document_id: Optional[int], text: Optional[str], mode: str
) -> dict:
    if document_id is not None:
        document = _get_ready_document(db, document_id)
        content = document.extracted_text or ""
        source_name = document.filename
    else:
        content = text or ""
        source_name = "Pasted text"

    truncated = len(content) > MAX_SUMMARY_CHARS
    content = content[:MAX_SUMMARY_CHARS]

    prompt = f"{SUMMARY_RULES[mode]}\n\nText:\n{content}"
    summary = generate_text(
        prompt,
        system_instruction=(
            "You summarize text. Use only the text given. Do not add outside facts."
        ),
    )
    return {
        "summary": summary,
        "mode": mode,
        "source_name": source_name,
        "truncated": truncated,
    }


# ---------------- Quiz generator ----------------
def _parse_quiz(raw: str, wanted: int) -> list[QuizQuestion]:
    """Turn the AI text into a list of valid questions."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    data = json.loads(cleaned)
    items = data.get("questions", []) if isinstance(data, dict) else data

    questions = []
    for item in items:
        try:
            questions.append(QuizQuestion(**item))
        except (ValidationError, TypeError):
            continue   # skip a broken question
    return questions[:wanted]


def create_quiz(
    db: Session,
    document_id: Optional[int],
    topic: Optional[str],
    num_questions: int,
    difficulty: str,
) -> dict:
    topic = (topic or "").strip()
    document = _get_ready_document(db, document_id) if document_id else None

    if topic:
        # Find the parts of your documents about this topic
        chunks = retrieve_chunks(db, embed_query(topic), 8, document_id)
        chunks = [c for c in chunks if c["similarity"] >= settings.MIN_SIMILARITY]
        if not chunks:
            raise ValueError("No content in your documents matches this topic.")
        content = "\n\n".join(c["content"] for c in chunks)
        source_name = document.filename if document else f"Topic: {topic}"
    else:
        content = (document.extracted_text or "")[:MAX_QUIZ_CHARS]
        source_name = document.filename

    prompt = (
        f"Create {num_questions} multiple-choice questions at {difficulty} difficulty "
        "using ONLY the content below.\n"
        "Each question must have exactly 4 options and exactly one correct option.\n"
        "Return ONLY valid JSON in this format:\n"
        '{"questions": [{"question": "...", "options": ["A", "B", "C", "D"], '
        '"correct_index": 0, "explanation": "..."}]}\n'
        "correct_index is the position (0 to 3) of the correct option.\n\n"
        f"Content:\n{content}"
    )

    # Try twice, because the AI sometimes returns broken JSON
    for attempt in (1, 2):
        raw = generate_text(prompt, temperature=0.4, json_mode=True)
        try:
            questions = _parse_quiz(raw, num_questions)
        except (json.JSONDecodeError, AttributeError):
            questions = []
        if questions:
            return {
                "source_name": source_name,
                "difficulty": difficulty,
                "questions": questions,
            }
        logger.warning("Quiz parse failed on attempt %s", attempt)

    raise AIServiceError("The AI returned an invalid quiz. Please try again.")


# ---------------- Recommendations ----------------
def create_recommendations(db: Session) -> str:
    profile = db.execute(select(Profile).limit(1)).scalar_one_or_none()
    goals = db.execute(
        select(Goal).where(Goal.status == "active").limit(10)
    ).scalars().all()
    documents = db.execute(
        select(Document).where(Document.status == "ready").limit(20)
    ).scalars().all()
    notes = db.execute(select(Note.title).limit(20)).scalars().all()

    interests = profile.interests if profile else []
    skills = profile.skills if profile else []
    preferences = profile.learning_preferences if profile else ""
    personal_goals = profile.personal_goals if profile else ""

    if not (interests or skills or goals or personal_goals):
        raise ValueError("Add interests, skills or goals first, so I can personalize.")

    # Only the information needed is sent (no name, no bio, no document text)
    prompt = (
        "Give 5 specific, practical suggestions for what this person should learn "
        "or do next. Base them ONLY on the information below. "
        "Do not invent progress or achievements. Keep each suggestion to 1 or 2 sentences.\n\n"
        f"Interests: {', '.join(interests) or 'not provided'}\n"
        f"Skills: {', '.join(skills) or 'not provided'}\n"
        f"Learning preferences: {preferences or 'not provided'}\n"
        f"Personal goals: {personal_goals or 'not provided'}\n"
        f"Active goals: {', '.join(g.title for g in goals) or 'none'}\n"
        f"Saved documents: {', '.join(d.filename for d in documents) or 'none'}\n"
        f"Saved note titles: {', '.join(notes) or 'none'}"
    )
    return generate_text(prompt, temperature=0.5)