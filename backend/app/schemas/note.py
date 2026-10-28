from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20000)
    category: str = Field(default="General", min_length=1, max_length=100)


class NoteUpdate(BaseModel):
    # All fields are optional: send only what you want to change
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=20000)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: str
    created_at: datetime
    updated_at: datetime