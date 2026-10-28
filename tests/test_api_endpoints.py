from unittest.mock import patch

from app.services.ai_service import AIServiceError
from app.services.rag_service import SessionNotFoundError
from app.services.study_service import NotFoundError

FAKE_ANSWER = {
    "answer": "RAG finds text first, then answers.",
    "answer_type": "document_grounded",
    "is_grounded": True,
    "sources": [
        {
            "document_id": 1,
            "document_name": "notes.pdf",
            "page_number": 1,
            "similarity": 0.55,
            "snippet": "RAG means retrieval...",
        }
    ],
    "session_id": 7,
}


# ---------- basic ----------
def test_root_is_running(client):
    assert client.get("/").status_code == 200


def test_health_returns_expected_fields(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    for key in ("status", "database_connected", "pgvector_enabled", "gemini_key_configured"):
        assert key in body
    assert body["status"] in ("ok", "degraded")


# ---------- /ai/ask ----------
def test_ask_returns_grounded_answer(client):
    with patch("app.routes.ai.ask_question", return_value=FAKE_ANSWER):
        response = client.post("/ai/ask", json={"question": "What is RAG?"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_grounded"] is True
    assert body["sources"][0]["document_name"] == "notes.pdf"
    assert body["session_id"] == 7


def test_ask_rejects_short_question(client):
    assert client.post("/ai/ask", json={"question": "hi"}).status_code == 422


def test_ask_rejects_placeholder_session_id_zero(client):
    response = client.post("/ai/ask", json={"question": "What is RAG?", "session_id": 0})
    assert response.status_code == 422


def test_ask_unknown_session_gives_404(client):
    with patch("app.routes.ai.ask_question", side_effect=SessionNotFoundError("missing")):
        response = client.post("/ai/ask", json={"question": "What is RAG?", "session_id": 99})
    assert response.status_code == 404


def test_ask_gemini_failure_gives_502(client):
    with patch("app.routes.ai.ask_question", side_effect=AIServiceError("busy")):
        response = client.post("/ai/ask", json={"question": "What is RAG?"})
    assert response.status_code == 502


# ---------- summarize and quiz validation ----------
def test_summarize_needs_exactly_one_input(client):
    neither = client.post("/ai/summarize", json={"mode": "short"})
    both = client.post(
        "/ai/summarize", json={"mode": "short", "text": "hello", "document_id": 1}
    )
    assert neither.status_code == 422
    assert both.status_code == 422


def test_summarize_missing_document_gives_404(client):
    with patch("app.routes.ai.summarize_content", side_effect=NotFoundError("Document not found.")):
        response = client.post("/ai/summarize", json={"document_id": 5, "mode": "short"})
    assert response.status_code == 404


def test_quiz_needs_document_or_topic(client):
    assert client.post("/ai/generate-quiz", json={}).status_code == 422


def test_quiz_question_count_is_limited(client):
    response = client.post(
        "/ai/generate-quiz", json={"topic": "python", "num_questions": 99}
    )
    assert response.status_code == 422


# ---------- upload validation ----------
def test_upload_rejects_wrong_file_type(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("virus.exe", b"abc", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_upload_rejects_empty_file(client):
    response = client.post(
        "/documents/upload", files={"file": ("empty.txt", b"", "text/plain")}
    )
    assert response.status_code == 400


# ---------- other validation ----------
def test_note_needs_a_title(client):
    response = client.post("/notes", json={"title": "", "content": "text"})
    assert response.status_code == 422


def test_goal_status_must_be_valid(client):
    response = client.put("/goals/1", json={"status": "weird"})
    assert response.status_code == 422


def test_quiz_score_cannot_be_above_total(client):
    response = client.post(
        "/quiz/attempts",
        json={"source_name": "x", "difficulty": "easy", "score": 5, "total": 3},
    )
    assert response.status_code == 422