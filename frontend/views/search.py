import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.helpers import fetch
from utils.styles import badge, page_header, safe

page_header("Semantic Search", "Find content by meaning, not just exact words")

documents = fetch(api_client.list_documents, default=[])
ready = {d["id"]: d["filename"] for d in documents if d["status"] == "ready"}

with st.form("search_form"):
    query = st.text_input("What are you looking for?", placeholder="e.g. database skills")
    c1, c2, c3 = st.columns(3)
    top_k = c1.slider("Max results", 1, 20, 5)
    document_id = c2.selectbox(
        "Limit to one document",
        [None] + list(ready),
        format_func=lambda i: "All documents and notes" if i is None else ready[i],
    )
    include_notes = c3.checkbox("Include notes", value=True)
    submitted = st.form_submit_button("Search", type="primary")

if submitted:
    if len(query.strip()) < 2:
        st.warning("Please type at least 2 characters.")
    else:
        with st.spinner("Searching..."):
            try:
                response = api_client.search(query.strip(), top_k, document_id, include_notes)
                st.session_state["search_state"] = {
                    "query": query.strip(),
                    "results": response["results"],
                }
            except ApiError as error:
                st.error(str(error))

state = st.session_state.get("search_state")
if state:
    st.subheader(f"Results for '{state['query']}'")
    if not state["results"]:
        st.info(
            "No matches found. Try different words. Only results above the "
            "similarity threshold are shown."
        )

    for index, result in enumerate(state["results"]):
        with st.container(border=True):
            kind = "success" if result["item_type"] == "document" else "info"
            page = f" · page {result['page_number']}" if result.get("page_number") else ""
            st.markdown(
                f"{badge(result['item_type'].capitalize(), kind)} &nbsp; "
                f"**{safe(result['title'])}**{page}",
                unsafe_allow_html=True,
            )
            st.progress(min(max(result["similarity"], 0.0), 1.0))
            st.caption(f"Similarity score: {result['similarity']:.2f}")
            st.write(result["content"])
            if st.button("Open in My Knowledge", key=f"open_{index}"):
                st.session_state["open_item"] = (result["item_type"], result["item_id"])
                st.switch_page("views/knowledge.py")