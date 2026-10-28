import html

import streamlit as st

CSS = """
<style>
.block-container { padding-top: 2rem; max-width: 1200px; }
footer { visibility: hidden; }

.page-title { font-size: 1.9rem; font-weight: 700; margin-bottom: 0.1rem; }
.page-subtitle { opacity: 0.7; margin-bottom: 1.2rem; }

/* Metric cards */
[data-testid="stMetric"] {
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-radius: 12px;
    padding: 14px 16px;
    background: rgba(128, 128, 128, 0.06);
}

/* Small status badges */
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600;
}
.badge-success { background: rgba(34, 160, 90, 0.18); color: #1f9d55; }
.badge-warning { background: rgba(245, 158, 11, 0.18); color: #d98a00; }
.badge-error   { background: rgba(220, 53, 69, 0.18); color: #dc3545; }
.badge-info    { background: rgba(59, 130, 246, 0.18); color: #3b82f6; }
.badge-neutral { background: rgba(128, 128, 128, 0.18); color: inherit; }

/* Phones and small screens */
@media (max-width: 768px) {
    .block-container { padding: 1rem; }
    .page-title { font-size: 1.5rem; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def safe(text) -> str:
    """Escape text before putting it inside HTML."""
    return html.escape(str(text))


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"<div class='page-title'>{safe(title)}</div>"
        f"<div class='page-subtitle'>{safe(subtitle)}</div>",
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str = "neutral") -> str:
    """Return badge HTML. Show it with st.markdown(..., unsafe_allow_html=True)."""
    return f"<span class='badge badge-{kind}'>{safe(text)}</span>"


def status_badge(status: str) -> str:
    kinds = {"ready": "success", "processing": "warning", "failed": "error"}
    return badge(status.capitalize(), kinds.get(status, "neutral"))