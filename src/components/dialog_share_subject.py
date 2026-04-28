import streamlit as st

import segno
import io
from src.ui.base_layout import render_heading


@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    app_domain = "snapclass-main.streamlit.app"
    join_url = f"{app_domain}/?join-code={subject_code}"

    render_heading("Scan to Join", level=2)

    qr = segno.make(join_url)

    out = io.BytesIO()

    qr.save(out, kind='png', scale=10, border=1)

    col1, col2 = st.columns(2)

    with col1:
        render_heading("Copy Link", level=3)
        st.code(join_url, language="text")
        st.code(subject_code, language="text")
        st.info('Copy this link to share on Whatsapp or Email')

    with col2:
        render_heading("Scan to Join", level=3)
        st.image(out.getvalue(), caption='QRCODE for class joining')

        
