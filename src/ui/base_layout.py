import streamlit as st


def style_background_home():
    st.markdown("""
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

            @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

            #MainMenu, footer, header {
                visibility: hidden;
            }

            .block-container {
                padding-top: 1.5rem !important;
                padding-bottom: 1rem !important;
            }

            h1 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 3.5rem !important;
                line-height: 1.1 !important;
                margin-bottom: 0rem !important;
                text-align: center !important;
            }

            h2 {
                font-family: 'Outfit', sans-serif !important;
                font-size: 2rem !important;
                line-height: 1 !important;
                margin-bottom: 0rem !important;
                color: black !important;
                font-weight: 700 !important;
            }

            h3, h4, h5, h6, p, span {
                font-family: 'Outfit', sans-serif !important;
                color: black !important;
            }

            button {
                border-radius: 1.5rem !important;
                background-color: #5865F2 !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                font-family: 'Outfit', sans-serif !important;
                font-weight: 600 !important;
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