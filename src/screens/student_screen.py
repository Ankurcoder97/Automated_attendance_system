import streamlit as st
from io import BytesIO

from src.ui.base_layout import render_heading, style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject
import time

from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card

def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        render_heading(f"Welcome, {student_data['name']}", level=3)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            del st.session_state.student_data 
            st.rerun()


    st.space()

    c1, c2 =st.columns(2)
    with c1:
        render_heading('Your Enrolled Subjects', level=2)
    with c2:
        if st.button('Enroll in Subject', type='primary', width='stretch'):
            enroll_dialog()


    st.divider()


    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log['subject_id']

        if sid not in stats_map:
            stats_map[sid] = {"total":0, "attended": 0}

        stats_map[sid]['total'] +=1

        if log.get('is_present'):
            stats_map[sid]['attended'] += 1


    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']
        subject_name = sub['name']


        stats = stats_map.get(sid,{"total":0, "attended": 0} )
        def unenroll_button(subject_id=sid, button_subject_name=subject_name):
                if st.button(
                    "Unenroll from this course",
                    type='tertiary',
                    width='stretch',
                    icon=':material/delete_forever:',
                    key=f"unenroll_{student_id}_{subject_id}",
                ):
                    unenroll_student_to_subject(student_id, subject_id)
                    st.toast(f"Unenrolled from {button_subject_name} successfully!")
                    st.rerun()

        with cols[i % 2]:

            subject_card(
                name = sub['name'],
                code =sub['subject_code'],
                section = sub['section'],
                stats = [
                    ('📅', 'Total', stats['total']),
                    ('✅', 'Attended', stats['attended']),
                ],
                footer_callback=unenroll_button
            )
    footer_dashboard()


def student_screen():


    style_background_dashboard()
    style_base_layout()


    if "student_data" in st.session_state:
        student_dashboard()
        return
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    render_heading('Login using FaceID', level=2, align='center')
    st.space()
    st.space()

    if 'student_registration_open' not in st.session_state:
        st.session_state.student_registration_open = False
    if 'student_registration_photo' not in st.session_state:
        st.session_state.student_registration_photo = None
    if 'student_face_scan_status' not in st.session_state:
        st.session_state.student_face_scan_status = None

    photo_source = st.camera_input("Position your face in the center")

    if photo_source:
        photo_bytes = photo_source.getvalue()
        img = np.array(Image.open(photo_source))

        with st.spinner('AI is scanning..'):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.session_state.student_registration_open = False
                st.session_state.student_registration_photo = None
                st.session_state.student_face_scan_status = 'no_face'
                st.warning('Face not found!')
            elif num_faces >1:
                st.session_state.student_registration_open = False
                st.session_state.student_registration_photo = None
                st.session_state.student_face_scan_status = 'multiple_faces'
                st.warning('Multiple faces found')
            else:
                st.session_state.student_registration_photo = photo_bytes
                if detected:
                    st.session_state.student_face_scan_status = 'recognized'
                    student_id = list(detected.keys())[0]
                    all_students = get_all_students()
                    student = next((s for s in all_students if s['student_id']==student_id), None)

                    if student and not st.session_state.student_registration_open:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'student'
                        st.session_state.student_data = student
                        st.toast(f"Welcome Back {student['name']}")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.session_state.student_face_scan_status = 'unrecognized'
                    st.session_state.student_registration_open = True

    if st.session_state.student_face_scan_status == 'unrecognized':
        st.info('Face not recognized! You might be a new student!')
    elif st.session_state.student_face_scan_status == 'recognized':
        st.caption('Face matched an existing profile. If this is incorrect, you can still register as a new student below.')

    can_offer_registration = (
        st.session_state.student_registration_photo is not None
        and st.session_state.student_face_scan_status in {'recognized', 'unrecognized'}
    )

    if can_offer_registration and not st.session_state.student_registration_open:
        if st.button('Register as New Student', type='secondary', width='stretch'):
            st.session_state.student_registration_open = True
            st.rerun()

    if st.session_state.student_registration_open:
        with st.container(border=True):
            render_heading('Register new Profile', level=2)
            new_name = st.text_input("Enter your name", placeholder='E.g. Ankur Banerjee')

            render_heading('Optional : Voice Enrollment', level=3)
            st.info("Enroll your for voice only attendance")


            audio_data = None

            try:
                audio_data = st.audio_input('Record a short phrase like I am present, My name is Akash.')
            except Exception:
                st.error('Audio Data failed!')

            if st.button('Create Account', type='primary'):
                if new_name:
                    with st.spinner('Creating profile..'):
                        saved_photo = st.session_state.student_registration_photo

                        if not saved_photo:
                            st.error('Please capture your photo again before creating an account.')
                            footer_dashboard()
                            return

                        img = np.array(Image.open(BytesIO(saved_photo)))
                        encodings= get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()

                            voice_emb = None
                            if audio_data:
                                voice_emb = get_voice_embedding(audio_data.read())

                            response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)

                            if response_data:
                                train_classifier()
                                st.session_state.student_registration_open = False
                                st.session_state.student_registration_photo = None
                                st.session_state.student_face_scan_status = None
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]
                                st.toast(f'Profile Created! Hi {new_name}!')
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error('Couldnt capture your facial features for registration')

                else:
                    st.warning('Please enter your name!')


        
    footer_dashboard()
