from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuizAttemptIn(BaseModel):
    source_name: str = Field(min_length=1, max_length=255)
    difficulty: str = Field(max_length=20)
    score: int = Field(ge=0)
    total: int = Field(ge=1)
    details: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def score_not_above_total(self):
        if self.score > self.total:
            raise ValueError("score cannot be bigger than total")
        return self


class QuizAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    difficulty: str
    score: int
    total: int
    created_at: datetime