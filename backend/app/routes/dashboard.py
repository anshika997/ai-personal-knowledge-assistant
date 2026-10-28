from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.document import Document
from app.models.goal import Goal, Task
from app.models.note import Note
from app.models.quiz import QuizAttempt

router = APIRouter(tags=["Dashboard"])


def _count(db: Session, statement) -> int:
    return db.scalar(statement) or 0


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    # ---- Counts ----
    documents = _count(db, select(func.count()).select_from(Document).where(Document.status == "ready"))
    notes = _count(db, select(func.count()).select_from(Note))
    goals_active = _count(db, select(func.count()).select_from(Goal).where(Goal.status == "active"))
    goals_done = _count(db, select(func.count()).select_from(Goal).where(Goal.status == "completed"))
    tasks_total = _count(db, select(func.count()).select_from(Task))
    tasks_done = _count(db, select(func.count()).select_from(Task).where(Task.is_completed.is_(True)))
    quiz_count = _count(db, select(func.count()).select_from(QuizAttempt))

    # Average quiz score in percent (None if no quiz yet)
    average = db.scalar(select(func.avg(QuizAttempt.score * 100.0 / QuizAttempt.total)))

    # ---- Recent items ----
    recent_docs = db.execute(
        select(Document).order_by(Document.created_at.desc()).limit(5)
    ).scalars().all()
    recent_notes = db.execute(
        select(Note).order_by(Note.updated_at.desc()).limit(5)
    ).scalars().all()
    recent_goals = db.execute(
        select(Goal).order_by(Goal.created_at.desc()).limit(5)
    ).scalars().all()
    recent_attempts = db.execute(
        select(QuizAttempt).order_by(QuizAttempt.created_at.desc()).limit(5)
    ).scalars().all()
    done_tasks = db.execute(
        select(Task).where(Task.is_completed.is_(True))
        .order_by(Task.completed_at.desc()).limit(5)
    ).scalars().all()

    # ---- Activity feed (built only from real records) ----
    activity = (
        [{"type": "Document uploaded", "title": d.filename, "at": d.created_at} for d in recent_docs]
        + [{"type": "Note saved", "title": n.title, "at": n.updated_at} for n in recent_notes]
        + [{"type": "Quiz taken", "title": f"{q.source_name} ({q.score}/{q.total})", "at": q.created_at} for q in recent_attempts]
        + [{"type": "Task completed", "title": t.title, "at": t.completed_at} for t in done_tasks if t.completed_at]
    )
    activity.sort(key=lambda item: item["at"], reverse=True)

    return {
        "counts": {
            "documents": documents,
            "notes": notes,
            "goals_active": goals_active,
            "goals_completed": goals_done,
            "tasks_total": tasks_total,
            "tasks_completed": tasks_done,
            "quizzes_taken": quiz_count,
            "average_quiz_score_percent": round(average, 1) if average is not None else None,
        },
        "recent_documents": [
            {"id": d.id, "filename": d.filename, "category": d.category,
             "status": d.status, "created_at": d.created_at}
            for d in recent_docs
        ],
        "recent_notes": [
            {"id": n.id, "title": n.title, "category": n.category, "updated_at": n.updated_at}
            for n in recent_notes
        ],
        "recent_goals": [
            {"id": g.id, "title": g.title, "status": g.status,
             "tasks_total": len(g.tasks),
             "tasks_completed": sum(1 for t in g.tasks if t.is_completed)}
            for g in recent_goals
        ],
        "recent_activity": activity[:8],
    }