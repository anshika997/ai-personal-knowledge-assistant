import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# Read .env from the project root (on Render, real environment variables are used)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")


class ApiError(Exception):
    """Raised when the backend returns an error or cannot be reached."""


def _error_message(response: requests.Response) -> str:
    """Turn a backend error response into a readable message."""
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        detail = None

    # Validation errors come as a list
    if isinstance(detail, list):
        parts = []
        for item in detail:
            where = ".".join(str(p) for p in item.get("loc", []) if p != "body")
            message = item.get("msg", "Invalid value")
            parts.append(f"{where}: {message}" if where else message)
        return "; ".join(parts)

    if detail:
        return str(detail)
    return f"Request failed with status {response.status_code}."


def _request(method: str, path: str, timeout: int = 90, **kwargs):
    """Send one request to the backend and return the JSON result."""
    url = f"{API_URL}{path}"
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.exceptions.ConnectionError:
        raise ApiError(
            f"Cannot reach the backend at {API_URL}. Make sure it is running."
        )
    except requests.exceptions.Timeout:
        raise ApiError(
            "The request took too long. The server may be starting up. Please try again."
        )
    except requests.exceptions.RequestException as error:
        raise ApiError(f"Request error: {error}")

    if not response.ok:
        raise ApiError(_error_message(response))

    if response.status_code == 204 or not response.content:
        return None
    return response.json()


# ---------------- Health and dashboard ----------------
def health():
    return _request("GET", "/health", timeout=90)


def get_dashboard():
    return _request("GET", "/dashboard")


# ---------------- Profile ----------------
def get_profile():
    return _request("GET", "/profile")


def update_profile(data: dict):
    return _request("PUT", "/profile", json=data)


def reset_profile():
    return _request("DELETE", "/profile")


# ---------------- Documents ----------------
def upload_document(filename: str, content: bytes, mime_type: Optional[str], category: str):
    return _request(
        "POST",
        "/documents/upload",
        timeout=300,   # the first upload loads the AI model, so it can be slow
        files={"file": (filename, content, mime_type or "application/octet-stream")},
        data={"category": category},
    )


def list_documents(category: Optional[str] = None):
    params = {"category": category} if category else None
    return _request("GET", "/documents", params=params)


def get_document(document_id: int):
    return _request("GET", f"/documents/{document_id}")


def update_document_category(document_id: int, category: str):
    return _request("PUT", f"/documents/{document_id}", json={"category": category})


def delete_document(document_id: int):
    return _request("DELETE", f"/documents/{document_id}")


# ---------------- Notes ----------------
def list_notes():
    return _request("GET", "/notes")


def create_note(title: str, content: str, category: str):
    return _request(
        "POST", "/notes", timeout=120,
        json={"title": title, "content": content, "category": category},
    )


def update_note(note_id: int, title: str, content: str, category: str):
    return _request(
        "PUT", f"/notes/{note_id}", timeout=120,
        json={"title": title, "content": content, "category": category},
    )


def delete_note(note_id: int):
    return _request("DELETE", f"/notes/{note_id}")


# ---------------- AI ----------------
def ask(question: str, session_id: Optional[int] = None, document_id: Optional[int] = None):
    body: dict = {"question": question}
    if session_id:
        body["session_id"] = session_id
    if document_id:
        body["document_id"] = document_id
    return _request("POST", "/ai/ask", timeout=180, json=body)


def clear_session(session_id: int):
    return _request("DELETE", f"/ai/sessions/{session_id}")


def summarize(mode: str, document_id: Optional[int] = None, text: Optional[str] = None):
    body: dict = {"mode": mode}
    if document_id is not None:
        body["document_id"] = document_id
    else:
        body["text"] = text
    return _request("POST", "/ai/summarize", timeout=180, json=body)


def generate_quiz(
    num_questions: int,
    difficulty: str,
    document_id: Optional[int] = None,
    topic: Optional[str] = None,
):
    body: dict = {"num_questions": num_questions, "difficulty": difficulty}
    if document_id is not None:
        body["document_id"] = document_id
    if topic:
        body["topic"] = topic
    return _request("POST", "/ai/generate-quiz", timeout=180, json=body)


def recommendations():
    return _request("POST", "/ai/recommendations", timeout=180)


# ---------------- Search ----------------
def search(query: str, top_k: int = 5, document_id: Optional[int] = None, include_notes: bool = True):
    body: dict = {"query": query, "top_k": top_k, "include_notes": include_notes}
    if document_id is not None:
        body["document_id"] = document_id
    return _request("POST", "/search", timeout=120, json=body)


# ---------------- Quiz attempts ----------------
def save_quiz_attempt(source_name: str, difficulty: str, score: int, total: int, details: list):
    return _request(
        "POST", "/quiz/attempts",
        json={
            "source_name": source_name, "difficulty": difficulty,
            "score": score, "total": total, "details": details,
        },
    )


def list_quiz_attempts():
    return _request("GET", "/quiz/attempts")


# ---------------- Goals and tasks ----------------
def list_goals():
    return _request("GET", "/goals")


def create_goal(title: str, description: str, target_date: Optional[str] = None):
    body: dict = {"title": title, "description": description}
    if target_date:
        body["target_date"] = target_date
    return _request("POST", "/goals", json=body)


def update_goal(goal_id: int, **fields):
    return _request("PUT", f"/goals/{goal_id}", json=fields)


def delete_goal(goal_id: int):
    return _request("DELETE", f"/goals/{goal_id}")


def add_task(goal_id: int, title: str):
    return _request("POST", f"/goals/{goal_id}/tasks", json={"title": title})


def update_task(task_id: int, **fields):
    return _request("PUT", f"/tasks/{task_id}", json=fields)


def delete_task(task_id: int):
    return _request("DELETE", f"/tasks/{task_id}")