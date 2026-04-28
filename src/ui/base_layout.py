import streamlit as st



def style_base_layout():
    st.markdown("""
        <style>

        /* Hide Streamlit UI */
        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            padding-top: 1.5rem !important;
        }

        /* Fonts */
        h1, h2 {
            font-family: 'Climate Crisis', sans-serif !important;
        }

        h3, h4, p {
            font-family: 'Outfit', sans-serif;
        }

        /* ✅ PRIMARY BUTTON FIX */
        .stButton > button {
            border-radius: 1.5rem !important;
            background-color: #5865F2 !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: transform 0.25s ease-in-out !important;
        }

        /* Hover */
        .stButton > button:hover {
            transform: scale(1.05);
            background-color: #4752C4 !important;
        }

        /* OPTIONAL: secondary buttons (Streamlit uses data-baseweb attribute) */
        div[data-baseweb="button"] button {
            background-color: #EB459E !important;
        }

        </style>
    """, unsafe_allow_html=True)