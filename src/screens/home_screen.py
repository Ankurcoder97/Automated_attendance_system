import streamlit as st
from src.components.header import header_home
from src.components.footer import footer_home
from src.ui.base_layout import render_heading, style_base_layout, style_background_home
def home_screen():


    style_base_layout()
    style_background_home()
    
    header_home()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_heading("I'm Student", level=3, color="#FFFFFF")
        st.image("https://i.ibb.co/844D9Lrt/mascot-student.png", width=120)
        if st.button('Student Portal', type='primary', icon=':material/arrow_outward:', icon_position='right'):
            st.session_state['login_type']='student'
            st.rerun()

    with col2:
        render_heading("I'm Teacher", level=3, color="#FFFFFF")
        st.image("https://i.ibb.co/CsmQQV6X/mascot-prof.png", width=145)
        if st.button('Teacher Portal', type='primary', icon=':material/arrow_outward:', icon_position='right'):
            st.session_state['login_type']='teacher'
            st.rerun()

    footer_home()
