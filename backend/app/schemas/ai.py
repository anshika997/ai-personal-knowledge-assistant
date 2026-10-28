from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ---------- Ask (RAG) ----------
class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    session_id: Optional[int] = Field(default=None, ge=1)    # reuse a chat session
    top_k: Optional[int] = Field(default=None, ge=1, le=10)
    document_id: Optional[int] = Field(default=None, ge=1)   # search one document only


class SourceItem(BaseModel):
    document_id: int
    document_name: str
    page_number: Optional[int] = None
    similarity: float
    snippet: str


class AskResponse(BaseModel):
    answer: str
    answer_type: str   # "document_grounded" or "not_found_in_documents"
    is_grounded: bool
    sources: list[SourceItem]
    session_id: int


# ---------- Summarize ----------
class SummarizeRequest(BaseModel):
    document_id: Optional[int] = Field(default=None, ge=1)
    text: Optional[str] = Field(default=None, max_length=50000)
    mode: Literal["short", "detailed", "key_points"] = "short"

    @model_validator(mode="after")
    def need_exactly_one_input(self):
        has_text = bool(self.text and self.text.strip())
        has_document = self.document_id is not None
        if has_text == has_document:
            raise ValueError("Send either document_id or text (only one of them).")
        return self


class SummarizeResponse(BaseModel):
    summary: str
    mode: str
    source_name: str
    truncated: bool   # True if the text was too long and was cut


# ---------- Quiz ----------
class QuizRequest(BaseModel):
    document_id: Optional[int] = Field(default=None, ge=1)
    topic: Optional[str] = Field(default=None, max_length=200)
    num_questions: int = Field(default=5, ge=1, le=10)
    difficulty: Literal["easy", "medium", "hard"] = "medium"

    @model_validator(mode="after")
    def need_document_or_topic(self):
        has_topic = bool(self.topic and self.topic.strip())
        if self.document_id is None and not has_topic:
            raise ValueError("Send a document_id, a topic, or both.")
        return self


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)   # position of the right option
    explanation: str = ""


class QuizResponse(BaseModel):
    source_name: str
    difficulty: str
    questions: list[QuizQuestion]


# ---------- Recommendations ----------
class RecommendationResponse(BaseModel):
    recommendations: str