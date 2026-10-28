from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import semantic_search

router = APIRouter(prefix="/search", tags=["Semantic Search"])


@router.post("", response_model=SearchResponse)
def search(request: SearchRequest, db: Session = Depends(get_db)):
    results = semantic_search(
        db=db,
        query=request.query.strip(),
        top_k=request.top_k,
        document_id=request.document_id,
        include_notes=request.include_notes,
    )
    return {"query": request.query, "results": results}