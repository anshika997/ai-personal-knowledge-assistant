import streamlit as st

from utils.helpers import backend_status
from utils.styles import inject_css

st.set_page_config(
    page_title="AI Personal Knowledge Assistant",
    page_icon="🧠",
    layout="wide",
)
inject_css()

navigation = st.navigation(
    {
        "Overview": [
            st.Page("views/dashboard.py", title="Dashboard", icon="🏠", default=True),
        ],
        "Knowledge": [
            st.Page("views/upload.py", title="Upload Knowledge", icon="📤"),
            st.Page("views/knowledge.py", title="My Knowledge", icon="📚"),
            st.Page("views/search.py", title="Semantic Search", icon="🔎"),
        ],
        "AI Tools": [
            st.Page("views/assistant.py", title="AI Assistant", icon="🤖"),
            st.Page("views/summarizer.py", title="AI Summarizer", icon="📝"),
            st.Page("views/quiz.py", title="Quiz Generator", icon="❓"),
        ],
        "Personal": [
            st.Page("views/profile.py", title="Personal Profile", icon="👤"),
            st.Page("views/goals.py", title="Goals and Progress", icon="🎯"),
        ],
        "System": [
            st.Page("views/settings.py", title="Settings", icon="⚙️"),
        ],
    }
)

# Show whether the backend is reachable
status = backend_status()
with st.sidebar:
    st.divider()
    if status["ok"] and status["data"].get("status") == "ok":
        st.success("Backend connected")
    elif status["ok"]:
        st.warning("Backend is running, but the database has a problem. See Settings.")
    else:
        st.error("Backend not reachable. See Settings.")

navigation.run()