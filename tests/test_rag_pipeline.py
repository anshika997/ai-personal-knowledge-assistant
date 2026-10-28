import pytest

from app.core.config import settings
from app.models.chat import ChatMessage, ChatSession
from app.services import rag_service

CHUNK = {
    "document_id": 1,
    "document_name": "cv.pdf",
    "page_number": 2,
    "content": "Python and SQL skills",
    "similarity": 0.6,
}


class FakeResult:
    def scalars(self):
        return self

    def all(self):
        return []


class FakeDB:
    """A tiny fake database session."""

    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for obj in self.added:
            if isinstance(obj, ChatSession) and obj.id is None:
                obj.id = 1

    def get(self, model, key):
        session = ChatSession(title="old chat")
        session.id = key
        return session

    def execute(self, statement):
        return FakeResult()

    def commit(self):
        self.commits += 1


@pytest.fixture(autouse=True)
def base_setup(monkeypatch):
    monkeypatch.setattr(settings, "MIN_SIMILARITY", 0.25)
    monkeypatch.setattr(rag_service, "embed_query", lambda text: [0.0] * 384)


def must_not_be_called(*args, **kwargs):
    raise AssertionError("Gemini should not be called here")


def test_grounded_answer_with_sources(monkeypatch):
    monkeypatch.setattr(rag_service, "retrieve_chunks", lambda db, v, k, d=None: [CHUNK])
    monkeypatch.setattr(
        rag_service, "generate_text", lambda prompt, system=None, **kw: "She knows Python."
    )
    db = FakeDB()

    result = rag_service.ask_question(db, "What skills?")

    assert result["is_grounded"] is True
    assert result["answer_type"] == "document_grounded"
    assert result["answer"] == "She knows Python."
    assert result["sources"][0]["document_name"] == "cv.pdf"
    assert result["sources"][0]["page_number"] == 2
    assert result["session_id"] == 1
    assert db.commits == 1
    # 1 chat session + 1 user message + 1 assistant message
    assert len(db.added) == 3


def test_no_chunks_means_not_found_and_no_gemini_call(monkeypatch):
    monkeypatch.setattr(rag_service, "retrieve_chunks", lambda db, v, k, d=None: [])
    monkeypatch.setattr(rag_service, "generate_text", must_not_be_called)

    result = rag_service.ask_question(FakeDB(), "Who won the World Cup?")

    assert result["is_grounded"] is False
    assert result["answer_type"] == "not_found_in_documents"
    assert result["sources"] == []


def test_low_similarity_chunks_are_ignored(monkeypatch):
    weak = {**CHUNK, "similarity": 0.10}
    monkeypatch.setattr(rag_service, "retrieve_chunks", lambda db, v, k, d=None: [weak])
    monkeypatch.setattr(rag_service, "generate_text", must_not_be_called)

    result = rag_service.ask_question(FakeDB(), "Something unrelated")

    assert result["is_grounded"] is False


def test_gemini_not_found_token_gives_not_grounded(monkeypatch):
    monkeypatch.setattr(rag_service, "retrieve_chunks", lambda db, v, k, d=None: [CHUNK])
    monkeypatch.setattr(rag_service, "generate_text", lambda prompt, system=None, **kw: "NOT_FOUND")

    result = rag_service.ask_question(FakeDB(), "What is the capital of France?")

    assert result["is_grounded"] is False
    assert result["sources"] == []


def test_follow_up_uses_previous_question_for_search(monkeypatch):
    searched = []

    def fake_embed(text):
        searched.append(text)
        return [0.0] * 384

    monkeypatch.setattr(rag_service, "embed_query", fake_embed)
    monkeypatch.setattr(
        rag_service, "_load_history",
        lambda db, session_id: [ChatMessage(role="user", content="What is Python?")],
    )
    monkeypatch.setattr(rag_service, "retrieve_chunks", lambda db, v, k, d=None: [])

    rag_service.ask_question(FakeDB(), "Tell me more", session_id=5)

    assert searched[0] == "What is Python? Tell me more"


def test_build_prompt_contains_source_label_question_and_context():
    prompt = rag_service.build_prompt("What skills?", [CHUNK], [])
    assert "[Source 1: cv.pdf, page 2]" in prompt
    assert "Python and SQL skills" in prompt
    assert "Question: What skills?" in prompt