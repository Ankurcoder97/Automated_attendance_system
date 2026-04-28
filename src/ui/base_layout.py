from html import escape
from pathlib import Path

import streamlit as st


_BASE_DIR = Path(__file__).resolve().parent
_CSS_FILE = _BASE_DIR / "styles" / "base_layout.css"


def _load_css() -> str:
    try:
        return _CSS_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def style_background_home():
    st.markdown(
        """
        <style>
            .stApp {
                background: #5865F2 !important;
            }

            .stApp div[data-testid="stColumn"] {
                background-color: #E0E3FF !important;
                padding: 2.5rem !important;
                border-radius: 5rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_background_dashboard():
    st.markdown(
        """
        <style>
            .stApp {
                background: #E0E3FF !important;
                color: #111111 !important;
            }

            .stApp label,
            .stApp p,
            .stApp [data-testid="stMarkdownContainer"],
            .stApp [data-testid="stMarkdownContainer"] p,
            .stApp [data-testid="stWidgetLabel"],
            .stApp [data-testid="stWidgetLabel"] *,
            .stApp [data-testid="stCameraInput"] label,
            .stApp [data-testid="stFileUploaderDropzoneInstructions"],
            .stApp [data-testid="stFileUploaderDropzoneInstructions"] * {
                color: #111111 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_base_layout():
    css = _load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_heading(text: str, level: int = 1, color: str | None = None, align: str = "left"):
    tag = f"h{min(max(level, 1), 4)}"
    class_name = f"snap-{tag}"
    style_parts = [f"text-align:{align}"]

    if color:
        style_parts.append(f"color:{color}")

    safe_text = escape(text).replace("\n", "<br/>")
    st.markdown(
        f"<{tag} class='{class_name}' style='{'; '.join(style_parts)}'>{safe_text}</{tag}>",
        unsafe_allow_html=True,
    )
