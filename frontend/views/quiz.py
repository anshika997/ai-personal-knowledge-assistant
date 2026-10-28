import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.helpers import fetch, fmt_time
from utils.styles import page_header

page_header("Quiz Generator", "Test yourself on your own documents")

# Keep the quiz in session memory while the user answers
st.session_state.setdefault("quiz", None)
st.session_state.setdefault("quiz_result", None)
st.session_state.setdefault("quiz_nonce", 0)   # changes for every new quiz

documents = fetch(api_client.list_documents, default=[])
ready = {d["id"]: d["filename"] for d in documents if d["status"] == "ready"}

if not ready:
    st.info("Upload a document first to create a quiz.")
    st.stop()

# ---------------- Settings ----------------
with st.container(border=True):
    document_id = st.selectbox(
        "Document (optional)",
        [None] + list(ready),
        format_func=lambda i: "None" if i is None else ready[i],
    )
    topic = st.text_input("Topic (optional)", placeholder="e.g. backend skills")
    c1, c2 = st.columns(2)
    number = c1.slider("Number of questions", 1, 10, 5)
    difficulty = c2.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)

    if st.button("Generate quiz", type="primary"):
        if document_id is None and not topic.strip():
            st.warning("Choose a document, enter a topic, or both.")
        else:
            with st.spinner("Creating your quiz..."):
                try:
                    st.session_state.quiz = api_client.generate_quiz(
                        number, difficulty, document_id, topic.strip() or None
                    )
                    st.session_state.quiz_result = None
                    st.session_state.quiz_nonce += 1
                except ApiError as error:
                    st.error(str(error))

quiz = st.session_state.quiz
result = st.session_state.quiz_result
nonce = st.session_state.quiz_nonce

# ---------------- Attempt the quiz ----------------
if quiz and result is None:
    st.subheader(f"Quiz: {quiz['source_name']} ({quiz['difficulty']})")

    with st.form(f"quiz_form_{nonce}"):
        for i, question in enumerate(quiz["questions"]):
            st.markdown(f"**Q{i + 1}. {question['question']}**")
            st.radio(
                "Choose an answer", question["options"], index=None,
                key=f"quiz_{nonce}_{i}", label_visibility="collapsed",
            )
        submitted = st.form_submit_button("Submit answers", type="primary")

    if submitted:
        score, details = 0, []
        for i, question in enumerate(quiz["questions"]):
            choice = st.session_state.get(f"quiz_{nonce}_{i}")
            options = question["options"]
            picked = options.index(choice) if choice in options else None
            correct = picked == question["correct_index"]
            score += 1 if correct else 0
            details.append(
                {
                    "question": question["question"],
                    "your_answer": choice,
                    "correct_answer": options[question["correct_index"]],
                    "is_correct": correct,
                    "explanation": question.get("explanation", ""),
                }
            )

        total = len(quiz["questions"])
        st.session_state.quiz_result = {"score": score, "total": total, "details": details}

        # Save the attempt so the dashboard shows real quiz statistics
        try:
            api_client.save_quiz_attempt(
                quiz["source_name"], quiz["difficulty"], score, total, details
            )
        except ApiError as error:
            st.warning(f"Your score could not be saved: {error}")
        st.rerun()

# ---------------- Show the result ----------------
if quiz and result is not None:
    st.subheader("Your result")
    st.metric("Score", f"{result['score']} / {result['total']}")
    st.progress(result["score"] / result["total"])
    st.caption("Unanswered questions count as wrong.")

    for i, item in enumerate(result["details"], start=1):
        with st.container(border=True):
            icon = "✅" if item["is_correct"] else "❌"
            st.markdown(f"{icon} **Q{i}. {item['question']}**")
            st.write(f"Your answer: {item['your_answer'] or 'Not answered'}")
            if not item["is_correct"]:
                st.write(f"Correct answer: {item['correct_answer']}")
            if item["explanation"]:
                st.caption(item["explanation"])

    if st.button("Retake this quiz"):
        st.session_state.quiz_result = None
        st.session_state.quiz_nonce += 1   # clears the old selected answers
        st.rerun()

# ---------------- Past attempts ----------------
attempts = fetch(api_client.list_quiz_attempts, default=[])
if attempts:
    st.subheader("Past attempts")
    st.table(
        [
            {
                "Source": a["source_name"],
                "Difficulty": a["difficulty"],
                "Score": f"{a['score']} / {a['total']}",
                "Date": fmt_time(a["created_at"]),
            }
            for a in attempts[:10]
        ]
    )