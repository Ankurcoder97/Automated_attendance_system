import streamlit as st

# ❌ COMMENT THESE
# from src.screens.teacher_screen import teacher_screen
# from src.screens.student_screen import student_screen
# from src.screens.home_screen import home_screen
# from src.components.dialog_auto_enroll import auto_enroll_dialog

# ✅ Keep ONLY this test
try:
    from src.database.config import supabase
    st.write("✅ Supabase is installed")
except Exception as e:
    st.write("❌ Supabase NOT installed:", e)