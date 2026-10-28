import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.helpers import fetch
from utils.styles import badge, page_header

page_header(
    "AI Assistant",
    "Ask questions. Answers come only from your uploaded documents.",
)

# ---- Chat memory for this browser session ----
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = None

documents = fetch(api_client.list_documents, default=[])
ready = [d for d in documents if d["status"] == "ready"]

if not ready:
    st.info("Upload at least one document before asking questions.")
    st.page_link("views/upload.py", label="Go to Upload Knowledge", icon="📤")
    st.stop()

names = {d["id"]: d["filename"] for d in ready}

# ---- Controls ----
col1, col2 = st.columns([3, 1])
scope = col1.selectbox(
    "Search in",
    [None] + list(names),
    format_func=lambda i: "All documents" if i is None else names[i],
)
if col2.button("Clear chat"):
    session_id = st.session_state.chat_session_id
    if session_id:
        try:
            api_client.clear_session(session_id)
        except ApiError:
            pass   # the screen is cleared anyway
    st.session_state.chat_messages = []
    st.session_state.chat_session_id = None
    st.rerun()


def render_body(message: dict) -> None:
    """Show one message. Must be called inside st.chat_message()."""
    st.markdown(message["content"])
    if message["role"] != "assistant":
        return

    if message.get("is_grounded"):
        st.markdown(badge("Based on your documents", "success"), unsafe_allow_html=True)
        sources = message.get("sources", [])
        with st.expander(f"Sources ({len(sources)})"):
            for source in sources:
                page = f" · page {source['page_number']}" if source.get("page_number") else ""
                st.markdown(
                    f"**{source['document_name']}**{page} · similarity {source['similarity']:.2f}"
                )
                st.caption(source["snippet"])
    else:
        st.markdown(
            badge("Not found in your documents (no guess made)", "warning"),
            unsafe_allow_html=True,
        )


def render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        render_body(message)


if not st.session_state.chat_messages:
    st.caption("Try: 'Summarize the main points' or 'What does the document say about ...?'")

for message in st.session_state.chat_messages:
    render_message(message)

# ---- New question ----
prompt = st.chat_input("Ask a question about your documents")
if prompt:
    user_message = {"role": "user", "content": prompt}
    st.session_state.chat_messages.append(user_message)
    render_message(user_message)

    with st.chat_message("assistant"):
        result, error_text = None, None
        with st.spinner("Searching your documents..."):
            try:
                result = api_client.ask(prompt, st.session_state.chat_session_id, scope)
            except ApiError as error:
                error_text = str(error)

        if result is None:
            st.error(error_text)
            st.session_state.chat_messages.pop()   # remove the unanswered question
            if "does not exist" in (error_text or ""):
                st.session_state.chat_session_id = None   # old chat was deleted
        else:
            assistant_message = {
                "role": "assistant",
                "content": result["answer"],
                "is_grounded": result["is_grounded"],
                "sources": result["sources"],
            }
            st.session_state.chat_session_id = result["session_id"]
            st.session_state.chat_messages.append(assistant_message)
            render_body(assistant_message)