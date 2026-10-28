from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.ai import (
    AskRequest, AskResponse, QuizRequest, QuizResponse,
    RecommendationResponse, SummarizeRequest, SummarizeResponse,
)
from app.services.ai_service import AIServiceError
from app.services.rag_service import SessionNotFoundError, ask_question, delete_session
from app.services.study_service import (
    NotFoundError, create_quiz, create_recommendations, summarize_content,
)

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, db: Session = Depends(get_db)):
    try:
        return ask_question(
            db=db,
            question=request.question.strip(),
            session_id=request.session_id,
            top_k=request.top_k,
            document_id=request.document_id,
        )
    except SessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except AIServiceError as error:
        raise HTTPException(status_code=502, detail=str(error))


@router.delete("/sessions/{session_id}", status_code=204)
def clear_chat(session_id: int, db: Session = Depends(get_db)):
    """Delete a chat session (used by the 'Clear chat' button)."""
    try:
        delete_session(db, session_id)
    except SessionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest, db: Session = Depends(get_db)):
    try:
        return summarize_content(db, request.document_id, request.text, request.mode)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except AIServiceError as error:
        raise HTTPException(status_code=502, detail=str(error))


@router.post("/generate-quiz", response_model=QuizResponse)
def generate_quiz(request: QuizRequest, db: Session = Depends(get_db)):
    try:
        return create_quiz(
            db, request.document_id, request.topic,
            request.num_questions, request.difficulty,
        )
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except AIServiceError as error:
        raise HTTPException(status_code=502, detail=str(error))


@router.post("/recommendations", response_model=RecommendationResponse)
def recommendations(db: Session = Depends(get_db)):
    try:
        return {"recommendations": create_recommendations(db)}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except AIServiceError as error:
        raise HTTPException(status_code=502, detail=str(error))