import streamlit as st


# -----------------------------------
# BASE STYLE (SAFE VERSION)
# -----------------------------------
def style_base_layout():
    st.markdown("""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis&family=Noto+Serif:wght@400;700&display=swap');

    /* Hide default Streamlit header */
    #MainMenu, footer, header {
        visibility: hidden;
    }

    .block-container {
        padding-top: 1.5rem !important;
    }

    /* ------------------------
       SAFE CUSTOM CLASSES ONLY
       ------------------------ */

    /* Main Title */
    .main-title h1 {
        font-family: 'Climate Crisis', sans-serif !important;
        font-size: 3.5rem !important;
        line-height: 0.9 !important;
        margin: 0 !important;
        color: black !important;
    }

    /* Section Title */
    .section-title h2 {
        font-family: 'Climate Crisis', sans-serif !important;
        font-size: 2rem !important;
        line-height: 1 !important;
        margin: 0 !important;
        color: black !important;
        letter-spacing: 2px !important;
    }

    /* Blue heading */
    .blue-title h2 {
        color: #5865F2 !important;
    }

    /* Normal text */
    .normal-text p {
        font-family: 'Noto Serif', serif !important;
        color: black !important;
        margin: 0 !important;
    }

    /* Home Card */
    .home-card {
        background: #E0E3FF !important;
        padding: 2.5rem !important;
        border-radius: 2rem !important;
    }

    /* Popup Modal */
    .popup-box {
        background: #050816 !important;
        padding: 2rem !important;
        border-radius: 2rem !important;
    }

    /* Popup title */
    .popup-title h2 {
        font-family: 'Climate Crisis', sans-serif !important;
        font-size: 2rem !important;
        color: white !important;
        margin-bottom: 1rem !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 1.5rem !important;
        background: #5865F2 !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        transition: 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: scale(1.03);
    }

    .stButton > button * {
        color: white !important;
    }

    /* Text Input */
    .stTextInput input {
        background: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
        border-radius: 12px !important;
    }

    .stTextInput input:focus {
        border: 2px solid #5865F2 !important;
        box-shadow: 0 0 0 2px rgba(88,101,242,0.15) !important;
    }

    </style>
    """, unsafe_allow_html=True)


# -----------------------------------
# HOME PAGE BACKGROUND
# -----------------------------------
def style_background_home():
    st.markdown("""
    <style>
    .stApp {
        background-color: #5856F2 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# -----------------------------------
# DASHBOARD BACKGROUND
# -----------------------------------
def style_background_dashboard():
    st.markdown("""
    <style>
    .stApp {
        background-color: #E0E3FF !important;
    }
    </style>
    """, unsafe_allow_html=True)


# -----------------------------------
# EXAMPLE USAGE
# -----------------------------------

style_base_layout()
style_background_dashboard()

st.markdown("""
<div class="popup-box">

    <div class="popup-title">
        <h2>Enroll in Subject</h2>
    </div>

    <div class="normal-text">
        <p>Enter the subject code provided by your teacher to enroll</p>
    </div>

</div>
""", unsafe_allow_html=True)

st.text_input("Subject Code", placeholder="Eg. CS101")

st.button("Enroll now")