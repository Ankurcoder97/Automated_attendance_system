import streamlit as st


# -----------------------------
# COMMON BASE STYLE (load once)
# -----------------------------
def style_base_layout():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis&family=Noto+Serif:ital,wght@0,100..900;1,100..900&display=swap');

        /* Hide Streamlit default menu */
        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            padding-top: 1.5rem !important;
        }

        /* Headings */
        h1 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 3.5rem !important;
            line-height: 0.9 !important;
            margin-bottom: 0rem !important;
            color: black !important;
        }

        h2 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 2rem !important;
            line-height: 0.9 !important;
            margin-bottom: 0rem !important;
            color: black !important;
            letter-spacing: 2px !important;
        }

        .head h2 {
            color: #5865F2 !important;
        }

        h3, h4, p {
            font-family: 'Noto Serif', serif !important;
            color: black !important;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 1.5rem !important;
            background: #5865F2 !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: transform 0.25s ease-in-out !important;
        }

        .stButton > button * {
            color: white !important;
        }

        .stButton > button:hover {
            transform: scale(1.05);
        }

        /* Secondary button */
        .stButton > button[kind="secondary"] {
            background: #EB459E !important;
        }

        /* Tertiary button */
        .stButton > button[kind="tertiary"] {
            background: black !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# -----------------------------
# HOME PAGE STYLE
# -----------------------------
def style_background_home():
    st.markdown(
        """
        <style>

        .stApp {
            background-color: #5856F2 !important;
        }

        div[data-testid="stColumn"] {
            background-color: #E0E3FF !important;
            padding: 2.5rem !important;
            border-radius: 2rem !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# -----------------------------
# DASHBOARD PAGE STYLE
# -----------------------------
def style_background_dashboard():
    st.markdown(
        """
        <style>

        .stApp {
            background-color: #E0E3FF !important;
        }

        /* Input fields */
        .stTextInput input {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ddd !important;
            border-radius: 12px !important;
        }

        .stTextInput input::placeholder {
            color: #777 !important;
        }

        .stTextInput input:focus {
            border: 2px solid #5865F2 !important;
            box-shadow: 0 0 0 2px rgba(88,101,242,0.15) !important;
        }

        [data-testid="stTextInput"] {
            background: transparent !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# -----------------------------
# IMPORTANT:
# Call order should be:
#
# style_base_layout()
# style_background_home()
#
# OR
#
# style_base_layout()
# style_background_dashboard()
#
# -----------------------------