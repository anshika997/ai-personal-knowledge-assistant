import streamlit as st

from utils import api_client
from utils.helpers import fetch, fmt_time, show_flash
from utils.styles import page_header, safe, status_badge

page_header("Dashboard", "An overview of your personal knowledge base")
show_flash()

data = fetch(api_client.get_dashboard)
if data is None:
    st.info("Could not load the dashboard. Check the backend status in Settings.")
    st.stop()

counts = data["counts"]

# ---- Numbers ----
col1, col2, col3 = st.columns(3)
col1.metric("Documents", counts["documents"])
col2.metric("Notes", counts["notes"])
col3.metric("Active goals", counts["goals_active"])

col4, col5, col6 = st.columns(3)
col4.metric("Tasks completed", f"{counts['tasks_completed']} / {counts['tasks_total']}")
col5.metric("Quizzes taken", counts["quizzes_taken"])
average = counts["average_quiz_score_percent"]
col6.metric("Average quiz score", f"{average}%" if average is not None else "No quizzes yet")

# ---- Quick actions ----
st.subheader("Quick actions")
a1, a2, a3, a4 = st.columns(4)
with a1:
    st.page_link("views/upload.py", label="Upload a document", icon="📤")
with a2:
    st.page_link("views/assistant.py", label="Ask the assistant", icon="🤖")
with a3:
    st.page_link("views/knowledge.py", label="Add a note", icon="📚")
with a4:
    st.page_link("views/goals.py", label="Manage goals", icon="🎯")

# ---- Recent documents and notes ----
left, right = st.columns(2)

with left:
    st.subheader("Recent documents")
    with st.container(border=True):
        if not data["recent_documents"]:
            st.caption("No documents yet. Upload your first document to get started.")
        for doc in data["recent_documents"]:
            st.markdown(
                f"**{safe(doc['filename'])}** &nbsp; {status_badge(doc['status'])}",
                unsafe_allow_html=True,
            )
            st.caption(f"{doc['category']} · {fmt_time(doc['created_at'])}")

with right:
    st.subheader("Recent notes")
    with st.container(border=True):
        if not data["recent_notes"]:
            st.caption("No notes yet. Add one in My Knowledge.")
        for note in data["recent_notes"]:
            st.markdown(f"**{note['title']}**")
            st.caption(f"{note['category']} · {fmt_time(note['updated_at'])}")

# ---- Goals and activity ----
left, right = st.columns(2)

with left:
    st.subheader("Goals")
    with st.container(border=True):
        if not data["recent_goals"]:
            st.caption("No goals yet. Create one in Goals and Progress.")
        for goal in data["recent_goals"]:
            total, done = goal["tasks_total"], goal["tasks_completed"]
            st.markdown(f"**{goal['title']}** ({goal['status']})")
            st.progress(done / total if total else 0.0)
            st.caption(f"{done} of {total} tasks done")

with right:
    st.subheader("Recent activity")
    with st.container(border=True):
        if not data["recent_activity"]:
            st.caption("No activity yet.")
        for item in data["recent_activity"]:
            st.markdown(f"**{item['type']}:** {item['title']}")
            st.caption(fmt_time(item["at"]))