import streamlit as st


def style_background_home():
    st.markdown("""
        <style>

            .stApp {
                background: #5865F2 !important;
            }

            /* Better column selector for Streamlit Cloud */
            div[data-testid="column"] {
                background-color: #E0E3FF !important;
                padding: 2rem !important;
                border-radius: 2rem !important;
            }

        </style>
    """, unsafe_allow_html=True)


def style_background_dashboard():
    st.markdown("""
        <style>

            .stApp {
                background: #E0E3FF !important;
            }

        </style>
    """, unsafe_allow_html=True)


def style_base_layout():
    st.markdown("""
        <style>

            /* Optional: safer to remove if font issue happens */
            @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

            /* Hide Streamlit default menu/footer/header */
            #MainMenu, footer, header {
                visibility: hidden;
            }

            /* Main page spacing */
            .block-container {
                padding-top: 1.5rem !important;
                padding-bottom: 1rem !important;
            }

            /* Stronger heading selectors for deployment */

            div[data-testid="stMarkdownContainer"] h1 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 3.5rem !important;
                line-height: 1.1 !important;
                margin-bottom: 0rem !important;
                color: white !important;
                text-align: center !important;
            }

            div[data-testid="stMarkdownContainer"] h2 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 2rem !important;
                line-height: 1 !important;
                margin-bottom: 0rem !important;
                color: black !important;
                text-align: center !important;
            }

            div[data-testid="stMarkdownContainer"] h3,
            div[data-testid="stMarkdownContainer"] h4,
            div[data-testid="stMarkdownContainer"] p,
            div[data-testid="stMarkdownContainer"] span {
                font-family: 'Outfit', sans-serif !important;
                color: black !important;
            }

            /* Safe button styling */

            div.stButton > button {
                border-radius: 1rem !important;
                background-color: #5865F2 !important;
                color: white !important;
                border: none !important;
                font-weight: 600 !important;
                min-height: 45px !important;
                transition: transform 0.25s ease-in-out !important;
            }

            button[kind="secondary"] {
                background-color: #EB459E !important;
                color: white !important;
            }

            button[kind="tertiary"] {
                background-color: black !important;
                color: white !important;
            }

            button:hover {
                transform: scale(1.05);
            }

        </style>
    """, unsafe_allow_html=True)