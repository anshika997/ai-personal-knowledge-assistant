# AI-Based Personal Knowledge Assistant

Upload your documents and notes, then ask questions, search by meaning, summarize,
take quizzes, and track learning goals. Answers come only from your own documents
(Retrieval-Augmented Generation), with source names and page numbers.

## Features
- Upload PDF, TXT and DOCX files (text is extracted, chunked and embedded)
- RAG chat with sources and follow-up questions
- Semantic search across documents and notes
- Summarizer (short, detailed, key points) and multiple-choice quiz generator
- Notes, profile, goals with tasks, and a dashboard built from real data

## Tech stack
Streamlit, FastAPI, Neon PostgreSQL + pgvector, Sentence Transformers (all-MiniLM-L6-v2),
Google Gemini API, PyMuPDF, python-docx, Render.

## How it works
Upload -> extract text -> split into ~800 character chunks (150 overlap) -> embed (384 numbers)
-> store in pgvector. For a question: embed it -> find the most similar chunks (cosine
similarity) -> send chunks and question to Gemini -> answer with sources. If nothing relevant
is found, the app says so instead of guessing.

## Folder structure
```text
backend/app/   main.py, core/, database/, models/, schemas/, routes/, services/, utils/
frontend/      app.py, views/ (10 pages), utils/ (api_client.py, helpers.py, styles.py)
tests/         pytest tests
postman/       build_collection.py creates the Postman collection
render.yaml    Render deployment config
```

## Local setup
1. Python 3.10 to 3.12 is recommended.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # Mac/Linux
   pip install -r requirements.txt
   ```
3. Create a Neon project at neon.tech and copy the connection string.
   (pgvector is enabled automatically by `init_db`.)
4. Get a Gemini API key from Google AI Studio and check the current model name in the Gemini docs.
5. Copy `.env.example` to `.env` and fill in the values. Keep `.env` out of Git.
6. Create the tables (from the `backend` folder):
   ```bash
   cd backend
   python -m app.database.init_db
   ```
7. Run the backend (terminal 1, from `backend`):
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
8. Run the frontend (terminal 2, from the project root):
   ```bash
   streamlit run frontend/app.py
   ```

## Testing the API
- Swagger UI: http://127.0.0.1:8000/docs (click an endpoint, Try it out, Execute).
- Postman: `cd postman && python build_collection.py`, then import
  `knowledge_assistant.postman_collection.json`. Change the `base_url` variable for a
  deployed server. Upload one document first, then run the folders in order.
- Automated tests (no real database or Gemini needed):
  ```bash
  pytest -v              # fast tests
  pytest -m slow -v      # also loads the real embedding model
  ```

## Deploy on Render
1. Push the code to GitHub (never commit `.env`).
2. In Render: New -> Blueprint -> choose the repo. `render.yaml` creates two services.
3. Enter the values it asks for: `DATABASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`,
   `ALLOWED_ORIGINS` (any value for now) and `API_URL` (any value for now).
4. When the backend is live, copy its URL (https://....onrender.com), set `API_URL` of the
   frontend service to it, and save. The frontend restarts.
5. Open the frontend URL and check Settings.
Start commands:
- Backend: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Frontend: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

## Known limitations
- Single user, no login. Authentication is not simulated.
- Original uploaded files are stored inside Neon (limit 10 MB each) because Render's disk
  is not permanent.
- Scanned (image-only) PDFs are not supported (no OCR).
- Free Render services sleep after 15 minutes idle, so the first request after a pause is slow.
- Embeddings run on a small CPU server, so large uploads can take a while.
- Chat memory in the UI lasts for the browser session; saved chats are not listed yet.

## Troubleshooting
| Problem | Fix |
|---|---|
| `DATABASE_URL is not set` | Put `.env` in the project root and fill in the values |
| Database connection or SSL error | Keep `?sslmode=require`, remove `&channel_binding=require` |
| `ModuleNotFoundError: app` | Run uvicorn from inside the `backend` folder |
| Gemini 502 or busy error | Check the key and `GEMINI_MODEL`; the app retries automatically |
| Everything answers "not found" | Lower `MIN_SIMILARITY` (for example 0.15) |
| Frontend says backend not reachable | Check `API_URL`; wait about a minute if the backend is waking up |
| Out of memory on Render | See the memory notes in the deployment section |