import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.helpers import fetch, fmt_size, fmt_time
from utils.styles import page_header

MAX_MB = 10   # the backend checks the real limit too

page_header("Upload Knowledge", "Add PDF, TXT or DOCX files to your knowledge base")

with st.container(border=True):
    uploaded = st.file_uploader("Choose a file", type=["pdf", "txt", "docx"])
    category = st.text_input("Category", value="General", max_chars=100)
    st.caption(
        f"Maximum size: {MAX_MB} MB. Scanned (image-only) PDFs are not supported "
        "because there is no text to read."
    )

    if st.button("Upload and process", type="primary", disabled=uploaded is None):
        if uploaded.size > MAX_MB * 1024 * 1024:
            st.error(f"This file is larger than {MAX_MB} MB.")
        else:
            with st.spinner(
                "Processing... The first upload can take a minute while the AI model loads."
            ):
                try:
                    document = api_client.upload_document(
                        uploaded.name,
                        uploaded.getvalue(),
                        uploaded.type,
                        category.strip() or "General",
                    )
                except ApiError as error:
                    if "already uploaded" in str(error):
                        st.warning(str(error))
                    else:
                        st.error(str(error))
                else:
                    st.success(
                        f"'{document['filename']}' is ready. It was split into "
                        f"{document['chunk_count']} chunks."
                    )

st.subheader("Processing status")
documents = fetch(api_client.list_documents, default=[])

if not documents:
    st.caption("No documents yet.")
else:
    rows = [
        {
            "File": d["filename"],
            "Type": d["file_type"].upper(),
            "Size": fmt_size(d["file_size"]),
            "Category": d["category"],
            "Status": d["status"].capitalize(),
            "Chunks": d["chunk_count"],
            "Uploaded": fmt_time(d["created_at"]),
        }
        for d in documents[:15]
    ]
    st.table(rows)

    for d in documents:
        if d["status"] == "failed":
            st.warning(
                f"'{d['filename']}' failed: {d['error_message']}. "
                "You can delete it in My Knowledge and try again."
            )