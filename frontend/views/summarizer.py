import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.helpers import fetch
from utils.styles import page_header

page_header("AI Summarizer", "Summarize a document or any text you paste")

MODES = {"Short summary": "short", "Detailed summary": "detailed", "Key points": "key_points"}

source = st.radio("What do you want to summarize?", ["Uploaded document", "Pasted text"], horizontal=True)
mode_label = st.selectbox("Summary type", list(MODES))

document_id, text = None, ""
if source == "Uploaded document":
    documents = fetch(api_client.list_documents, default=[])
    ready = {d["id"]: d["filename"] for d in documents if d["status"] == "ready"}
    if not ready:
        st.info("Upload a document first, or choose 'Pasted text'.")
    else:
        document_id = st.selectbox("Document", list(ready), format_func=lambda i: ready[i])
else:
    text = st.text_area("Paste your text here", height=220, max_chars=50000)

if st.button("Summarize", type="primary"):
    if source == "Uploaded document" and document_id is None:
        st.warning("Please choose a document.")
    elif source == "Pasted text" and not text.strip():
        st.warning("Please paste some text.")
    else:
        with st.spinner("Writing the summary..."):
            try:
                st.session_state["summary_result"] = api_client.summarize(
                    MODES[mode_label],
                    document_id=document_id,
                    text=text.strip() if source == "Pasted text" else None,
                )
            except ApiError as error:
                st.error(str(error))

result = st.session_state.get("summary_result")
if result:
    st.subheader(f"{mode_label}: {result['source_name']}")
    if result["truncated"]:
        st.warning("The text was very long, so only the first part was summarized.")
    with st.container(border=True):
        st.markdown(result["summary"])
    st.download_button(
        "Download summary", result["summary"], file_name="summary.txt", mime="text/plain"
    )