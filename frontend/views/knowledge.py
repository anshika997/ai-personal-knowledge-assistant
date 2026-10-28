import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.helpers import fetch, flash, fmt_size, fmt_time, show_flash
from utils.styles import page_header, status_badge

page_header("My Knowledge", "Browse and manage your documents and notes")
show_flash()

documents = fetch(api_client.list_documents, default=[])
notes = fetch(api_client.list_notes, default=[])

# If the user clicked "Open" in Semantic Search, select that item
open_item = st.session_state.pop("open_item", None)
if open_item:
    kind, item_id = open_item
    if kind == "document" and item_id in [d["id"] for d in documents]:
        st.session_state["knowledge_view"] = "Documents"
        st.session_state["doc_select"] = item_id
    elif kind == "note" and item_id in [n["id"] for n in notes]:
        st.session_state["knowledge_view"] = "Notes"
        st.session_state["note_select"] = item_id

view = st.radio(
    "Show", ["Documents", "Notes"], horizontal=True,
    key="knowledge_view", label_visibility="collapsed",
)

# ======================= DOCUMENTS =======================
if view == "Documents":
    if not documents:
        st.info("No documents yet. Upload one first.")
        st.page_link("views/upload.py", label="Go to Upload Knowledge", icon="📤")
        st.stop()

    categories = sorted({d["category"] for d in documents})
    chosen = st.selectbox("Filter by category", ["All"] + categories)
    shown = [d for d in documents if chosen == "All" or d["category"] == chosen]

    st.table(
        [
            {
                "ID": d["id"],
                "File": d["filename"],
                "Category": d["category"],
                "Status": d["status"].capitalize(),
                "Size": fmt_size(d["file_size"]),
                "Chunks": d["chunk_count"],
                "Uploaded": fmt_time(d["created_at"]),
            }
            for d in shown
        ]
    )

    ids = [d["id"] for d in shown]
    names = {d["id"]: d["filename"] for d in shown}
    if st.session_state.get("doc_select") not in ids:
        st.session_state.pop("doc_select", None)

    selected_id = st.selectbox(
        "Inspect a document", ids, format_func=lambda i: names[i], key="doc_select"
    )
    detail = fetch(api_client.get_document, selected_id)

    if detail:
        with st.container(border=True):
            st.markdown(status_badge(detail["status"]), unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Pages", detail["page_count"] if detail["page_count"] else "n/a")
            c2.metric("Chunks", detail["chunk_count"])
            c3.metric("Size", fmt_size(detail["file_size"]))

            st.text_area(
                "Preview (first 3000 characters)",
                value=detail["preview_text"],
                height=280,
                disabled=True,
                key=f"preview_{selected_id}",
            )

            new_category = st.text_input(
                "Category", value=detail["category"], key=f"cat_{selected_id}", max_chars=100
            )
            if st.button("Save category", key=f"savecat_{selected_id}"):
                try:
                    api_client.update_document_category(selected_id, new_category.strip())
                    flash("Category updated.")
                    st.rerun()
                except ApiError as error:
                    st.error(str(error))

            confirm = st.checkbox(
                "Yes, delete this document and all its chunks", key=f"confirm_doc_{selected_id}"
            )
            if st.button("Delete document", disabled=not confirm, key=f"deldoc_{selected_id}"):
                try:
                    api_client.delete_document(selected_id)
                    flash("Document deleted.")
                    st.rerun()
                except ApiError as error:
                    st.error(str(error))

# ======================= NOTES =======================
else:
    with st.expander("Add a new note", expanded=not notes):
        with st.form("new_note_form", clear_on_submit=True):
            title = st.text_input("Title", max_chars=200)
            category = st.text_input("Category", value="General", max_chars=100)
            content = st.text_area("Content", height=150, max_chars=20000)
            submitted = st.form_submit_button("Save note", type="primary")
        if submitted:
            if not title.strip() or not content.strip():
                st.warning("Please enter both a title and some content.")
            else:
                with st.spinner("Saving note..."):
                    try:
                        api_client.create_note(
                            title.strip(), content.strip(), category.strip() or "General"
                        )
                        flash("Note saved.")
                        st.rerun()
                    except ApiError as error:
                        st.error(str(error))

    if not notes:
        st.info("No notes yet. Add your first note above.")
        st.stop()

    categories = sorted({n["category"] for n in notes})
    chosen = st.selectbox("Filter by category", ["All"] + categories, key="note_filter")
    shown = [n for n in notes if chosen == "All" or n["category"] == chosen]

    ids = [n["id"] for n in shown]
    titles = {n["id"]: f"{n['title']}  ({n['category']})" for n in shown}
    if st.session_state.get("note_select") not in ids:
        st.session_state.pop("note_select", None)

    selected_id = st.selectbox(
        "Select a note", ids, format_func=lambda i: titles[i], key="note_select"
    )
    note = next(n for n in shown if n["id"] == selected_id)

    with st.container(border=True):
        st.caption(f"Last updated: {fmt_time(note['updated_at'])}")
        with st.form(f"edit_note_{selected_id}"):
            new_title = st.text_input("Title", value=note["title"], max_chars=200)
            new_category = st.text_input("Category", value=note["category"], max_chars=100)
            new_content = st.text_area("Content", value=note["content"], height=200, max_chars=20000)
            updated = st.form_submit_button("Update note", type="primary")
        if updated:
            if not new_title.strip() or not new_content.strip():
                st.warning("Title and content cannot be empty.")
            else:
                with st.spinner("Updating note..."):
                    try:
                        api_client.update_note(
                            selected_id, new_title.strip(), new_content.strip(),
                            new_category.strip() or "General",
                        )
                        flash("Note updated.")
                        st.rerun()
                    except ApiError as error:
                        st.error(str(error))

        confirm = st.checkbox("Yes, delete this note", key=f"confirm_note_{selected_id}")
        if st.button("Delete note", disabled=not confirm, key=f"delnote_{selected_id}"):
            try:
                api_client.delete_note(selected_id)
                flash("Note deleted.")
                st.rerun()
            except ApiError as error:
                st.error(str(error))