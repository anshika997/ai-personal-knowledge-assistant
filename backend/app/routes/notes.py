from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.services.embedding_service import embed_texts

router = APIRouter(prefix="/notes", tags=["Notes"])


def _make_embedding(title: str, content: str) -> list[float]:
    """Embedding of the note, used by semantic search."""
    return embed_texts([f"{title}\n{content}"])[0]


@router.post("", response_model=NoteOut, status_code=201)
def create_note(data: NoteCreate, db: Session = Depends(get_db)):
    note = Note(
        title=data.title.strip(),
        content=data.content.strip(),
        category=data.category.strip(),
        embedding=_make_embedding(data.title, data.content),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("", response_model=list[NoteOut])
def list_notes(category: Optional[str] = None, db: Session = Depends(get_db)):
    statement = select(Note).order_by(Note.updated_at.desc())
    if category:
        statement = statement.where(Note.category == category)
    return db.execute(statement).scalars().all()


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NoteUpdate, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")

    changes = data.model_dump(exclude_unset=True)   # only fields that were sent
    for field, value in changes.items():
        if value is not None:
            setattr(note, field, value.strip())

    # If the text changed, the meaning changed, so make a new embedding
    if "title" in changes or "content" in changes:
        note.embedding = _make_embedding(note.title, note.content)

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")
    db.delete(note)
    db.commit()