from datetime import datetime

import streamlit as st

from utils import api_client
from utils.api_client import ApiError


def fmt_time(value) -> str:
    """Turn an ISO time from the backend into a readable UTC time."""
    if not value:
        return "-"
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return moment.strftime("%d %b %Y, %H:%M") + " UTC"
    except ValueError:
        return str(value)


def fmt_size(size_in_bytes: int) -> str:
    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.0f} KB"
    return f"{size_in_bytes / (1024 * 1024):.1f} MB"


def fetch(call, *args, default=None, **kwargs):
    """Call the API. On error, show a message and return `default`."""
    try:
        return call(*args, **kwargs)
    except ApiError as error:
        st.error(str(error))
        return default


def flash(message: str, kind: str = "success") -> None:
    """Remember a message so it can be shown after st.rerun()."""
    st.session_state["_flash"] = (kind, message)


def show_flash() -> None:
    item = st.session_state.pop("_flash", None)
    if item:
        kind, message = item
        getattr(st, kind)(message)


@st.cache_data(ttl=20, show_spinner=False)
def backend_status() -> dict:
    """Check the backend. Cached for 20 seconds so pages stay fast."""
    try:
        return {"ok": True, "data": api_client.health()}
    except ApiError as error:
        return {"ok": False, "error": str(error)}