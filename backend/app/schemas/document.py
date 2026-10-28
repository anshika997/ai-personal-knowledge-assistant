from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class DocumentOut(BaseModel):
    # from_attributes lets Pydantic read data from database objects
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    file_size: int
    category: str
    status: str
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: int
    created_at: datetime


class DocumentDetail(DocumentOut):
    preview_text: str   # first part of the extracted text
class DocumentUpdate(BaseModel):
    category: str = Field(min_length=1, max_length=100)