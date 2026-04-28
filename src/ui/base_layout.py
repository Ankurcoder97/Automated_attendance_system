import streamlit as st



def style_background_home():

    st.markdown("""
        <style>

                .stApp {
                    background: #5865F2 !important;
                }

                .stApp div[data-testid="stColumn"]{
                    background-color:#E0E3FF !important;
                    padding:2.5rem !important;
                    border-radius: 5rem !important;
                    }
        </style>  

                """
            ,unsafe_allow_html=True)
    

def style_background_dashboard():

    st.markdown("""
        <style>

                .stApp {
                    background: #E0E3FF !important;
                }

        </style>  

                """
            ,unsafe_allow_html=True)
    

    

def style_base_layout():
    st.markdown("""
        <style>

            #MainMenu, footer, header {
                visibility: hidden;
            }

            .block-container {
                padding-top: 1.5rem !important;
                padding-bottom: 1rem !important;
            }

            h1 {
                font-family: Arial, sans-serif !important;
                font-size: 3rem !important;
                line-height: 1.2 !important;
                margin-bottom: 0rem !important;
                text-align: center !important;
                color: white !important;
                font-weight: 700 !important;
            }

            h2 {
                font-family: Arial, sans-serif !important;
                font-size: 2rem !important;
                line-height: 1 !important;
                margin-bottom: 0rem !important;
                color: black !important;
                font-weight: 700 !important;
            }

            h3, h4, h5, h6, p, span {
                font-family: Arial, sans-serif !important;
                color: black !important;
            }

            div.stButton > button {
            border-radius: 1rem !important;
            background-color: #5865F2 !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
            min-height: 45px !important;
        }

        </style>
    """, unsafe_allow_html=True)