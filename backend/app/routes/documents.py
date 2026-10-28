from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db
from app.models.document import Document
from app.schemas.document import DocumentDetail, DocumentOut, DocumentUpdate
from app.services.document_service import DuplicateDocumentError, process_document
from app.utils.file_validation import validate_upload

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentOut, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    category: str = Form("General"),
    db: Session = Depends(get_db),
):
    # Read at most (max size + 1) bytes, so huge files are rejected early
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content = file.file.read(max_bytes + 1)

    # Check the file type and size
    try:
        validate_upload(file.filename or "", len(content))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Process the file (extract, chunk, embed, store)
    try:
        return process_document(db, file.filename, content, category.strip() or "General")
    except DuplicateDocumentError as error:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This file was already uploaded as "
                f"'{error.document.filename}' (id {error.document.id})."
            ),
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.get("", response_model=list[DocumentOut])
def list_documents(category: Optional[str] = None, db: Session = Depends(get_db)):
    statement = select(Document).order_by(Document.created_at.desc())
    if category:
        statement = statement.where(Document.category == category)
    return db.execute(statement).scalars().all()


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    base = DocumentOut.model_validate(document).model_dump()
    preview = (document.extracted_text or "")[:3000]   # first 3000 characters
    return DocumentDetail(**base, preview_text=preview)

@router.put("/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: int, data: DocumentUpdate, db: Session = Depends(get_db)
):
    """Change the category of a document."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    document.category = data.category.strip()
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    db.delete(document)   # its chunks are removed too
    db.commit()