from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.quiz import QuizAttempt
from app.schemas.quiz import QuizAttemptIn, QuizAttemptOut

router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.post("/attempts", response_model=QuizAttemptOut, status_code=201)
def save_attempt(data: QuizAttemptIn, db: Session = Depends(get_db)):
    """Save the result after the user finishes a quiz."""
    attempt = QuizAttempt(**data.model_dump())
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/attempts", response_model=list[QuizAttemptOut])
def list_attempts(db: Session = Depends(get_db)):
    return db.execute(
        select(QuizAttempt).order_by(QuizAttempt.created_at.desc()).limit(50)
    ).scalars().all()