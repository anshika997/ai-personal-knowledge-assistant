import streamlit as st

from utils import api_client
from utils.api_client import API_URL, ApiError
from utils.helpers import backend_status
from utils.styles import badge, page_header

page_header("Settings", "Configuration status of your application")

if st.button("Re-check connection"):
    backend_status.clear()   # also refreshes the sidebar status

st.subheader("Backend connection")
st.write("Backend URL:")
st.code(API_URL)

try:
    health = api_client.health()
except ApiError as error:
    st.error(str(error))
    st.info("Start the backend, or fix API_URL in your .env file.")
else:
    def show(label: str, good: bool, good_text: str, bad_text: str) -> None:
        kind, text = ("success", good_text) if good else ("error", bad_text)
        st.markdown(f"**{label}:** {badge(text, kind)}", unsafe_allow_html=True)

    show("Database", health["database_connected"], "Connected", "Not connected")
    show("pgvector", health["pgvector_enabled"], "Enabled", "Not enabled")
    show("Gemini API key", health["gemini_key_configured"], "Configured", "Missing")
    st.markdown(f"**Gemini model:** `{health['gemini_model']}`")

st.subheader("Appearance")
st.write("Light and dark theme: open the menu at the top right of the page, then Settings.")

st.subheader("Upcoming (not built yet)")
st.markdown(
    "- User login and multiple users\n"
    "- OCR for scanned PDFs\n"
    "- Downloading the original uploaded files"
)