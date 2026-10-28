from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[int] = Field(default=None, ge=1)  # search one document only
    include_notes: bool = True


class SearchResult(BaseModel):
    item_type: str            # "document" or "note"
    item_id: int              # use it to open the document or note
    title: str
    page_number: Optional[int] = None
    similarity: float
    content: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]