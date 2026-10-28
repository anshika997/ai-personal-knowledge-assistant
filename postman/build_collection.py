# Run this file to create the Postman collection JSON.
import json

BASE = "{{base_url}}"


def tests(code, save=None):
    """Postman test lines: check the status code and optionally save an id."""
    lines = [f"pm.test('Status is {code}', function () {{ pm.response.to.have.status({code}); }});"]
    if save:
        variable, field = save
        lines.append(f"pm.collectionVariables.set('{variable}', pm.response.json().{field});")
    return lines


def req(name, method, path, body=None, form=None, code=200, save=None):
    request = {"method": method, "header": [], "url": BASE + path}
    if body is not None:
        request["header"].append({"key": "Content-Type", "value": "application/json"})
        request["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, indent=2),
            "options": {"raw": {"language": "json"}},
        }
    if form is not None:
        request["body"] = {"mode": "formdata", "formdata": form}
    return {
        "name": name,
        "request": request,
        "event": [{"listen": "test",
                   "script": {"type": "text/javascript", "exec": tests(code, save)}}],
    }


def folder(name, items):
    return {"name": name, "item": items}


collection = {
    "info": {
        "name": "AI Personal Knowledge Assistant",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "item": [
        folder("1 Health", [
            req("Health check", "GET", "/health"),
        ]),
        folder("2 Documents", [
            req("Upload document", "POST", "/documents/upload", code=201,
                save=("document_id", "id"),
                form=[{"key": "file", "type": "file", "src": []},
                      {"key": "category", "value": "General", "type": "text"}]),
            req("List documents", "GET", "/documents"),
            req("Get document", "GET", "/documents/{{document_id}}"),
            req("Change category", "PUT", "/documents/{{document_id}}",
                body={"category": "Study"}),
        ]),
        folder("3 AI Assistant", [
            req("Ask question", "POST", "/ai/ask", save=("session_id", "session_id"),
                body={"question": "What are the main topics in this document?"}),
            req("Ask follow-up (same session)", "POST", "/ai/ask",
                body={"question": "Explain the first one in more detail.",
                      "session_id": "{{session_id}}"}),
            req("Ask outside documents (expects not found)", "POST", "/ai/ask",
                body={"question": "Who won the football World Cup in 2010?"}),
            req("Summarize document", "POST", "/ai/summarize",
                body={"document_id": "{{document_id}}", "mode": "key_points"}),
            req("Summarize pasted text", "POST", "/ai/summarize",
                body={"text": "Paste any long text here to summarize it.", "mode": "short"}),
            req("Generate quiz", "POST", "/ai/generate-quiz",
                body={"document_id": "{{document_id}}", "num_questions": 3,
                      "difficulty": "easy"}),
            req("Recommendations", "POST", "/ai/recommendations"),
            req("Clear chat session", "DELETE", "/ai/sessions/{{session_id}}", code=204),
        ]),
        folder("4 Search", [
            req("Semantic search", "POST", "/search",
                body={"query": "programming skills", "top_k": 5, "include_notes": True}),
        ]),
        folder("5 Notes", [
            req("Create note", "POST", "/notes", code=201, save=("note_id", "id"),
                body={"title": "RAG basics",
                      "content": "RAG means retrieving relevant text first, then asking the AI to answer from it.",
                      "category": "AI"}),
            req("List notes", "GET", "/notes"),
            req("Update note", "PUT", "/notes/{{note_id}}",
                body={"content": "RAG = Retrieval-Augmented Generation."}),
            req("Delete note", "DELETE", "/notes/{{note_id}}", code=204),
        ]),
        folder("6 Profile", [
            req("Get profile", "GET", "/profile"),
            req("Update profile", "PUT", "/profile",
                body={"full_name": "Test User", "bio": "Computer science student",
                      "interests": ["AI", "Backend development"],
                      "skills": ["Python", "FastAPI", "SQL"],
                      "learning_preferences": "Short videos and hands-on projects",
                      "personal_goals": "Get a backend internship"}),
            req("Reset profile", "DELETE", "/profile", code=204),
        ]),
        folder("7 Goals and Tasks", [
            req("Create goal", "POST", "/goals", code=201, save=("goal_id", "id"),
                body={"title": "Learn RAG", "description": "Build a small RAG project",
                      "target_date": "2026-12-31"}),
            req("Add task", "POST", "/goals/{{goal_id}}/tasks", code=201,
                save=("task_id", "id"), body={"title": "Read about embeddings"}),
            req("Complete task", "PUT", "/tasks/{{task_id}}", body={"is_completed": True}),
            req("List goals", "GET", "/goals"),
            req("Complete goal", "PUT", "/goals/{{goal_id}}", body={"status": "completed"}),
            req("Delete task", "DELETE", "/tasks/{{task_id}}", code=204),
            req("Delete goal", "DELETE", "/goals/{{goal_id}}", code=204),
        ]),
        folder("8 Quiz attempts", [
            req("Save quiz attempt", "POST", "/quiz/attempts", code=201,
                body={"source_name": "My document", "difficulty": "easy",
                      "score": 2, "total": 3, "details": []}),
            req("List quiz attempts", "GET", "/quiz/attempts"),
        ]),
        folder("9 Dashboard", [
            req("Dashboard", "GET", "/dashboard"),
        ]),
    ],
    "variable": [
        {"key": "base_url", "value": "http://127.0.0.1:8000"},
        {"key": "document_id", "value": "1"},
        {"key": "note_id", "value": "1"},
        {"key": "goal_id", "value": "1"},
        {"key": "task_id", "value": "1"},
        {"key": "session_id", "value": "1"},
    ],
}

with open("knowledge_assistant.postman_collection.json", "w", encoding="utf-8") as file:
    json.dump(collection, file, indent=2)

print("Created knowledge_assistant.postman_collection.json")