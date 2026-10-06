import pandas as pd
import streamlit as st

try:
    from streamlit_webrtc import WebRtcMode, webrtc_streamer
except Exception:
    WebRtcMode = None
    webrtc_streamer = None

from src.database.db import (
    create_class_session,
    end_class_session,
    get_behaviour_events_for_session,
    get_enrolled_students,
    get_student_analytics_for_session,
)
from src.pipelines.behaviour_pipeline import ObservableBehaviourDetector
from src.pipelines.live_class_pipeline import LiveClassProcessor
from src.ui.base_layout import render_heading


def live_classroom_panel(teacher_id, selected_subject_id):
    _ensure_live_state()
    enrolled_students = get_enrolled_students(selected_subject_id)

    if not enrolled_students:
        st.warning("No students enrolled in this course.")
        return

    session = st.session_state.live_class_session
    is_running = bool(session and session.get("status") == "running")

    c1, c2, c3 = st.columns([1, 1, 2], vertical_alignment="bottom")
    with c1:
        if st.button("Start Class", type="primary", width="stretch", disabled=is_running):
            try:
                session = create_class_session(selected_subject_id, teacher_id)
                st.session_state.live_class_session = session
                st.session_state.live_class_processor = LiveClassProcessor(
                    session_id=session["id"],
                    subject_id=selected_subject_id,
                    enrolled_students=enrolled_students,
                )
                st.toast("Class started")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not start class. Apply the live analytics migration first. Details: {exc}")
    with c2:
        if st.button("End Class", type="secondary", width="stretch", disabled=not is_running):
            processor = st.session_state.get("live_class_processor")
            if processor:
                try:
                    processor.finalize()
                except Exception as exc:
                    st.warning(f"Class ended, but final attendance sync had an issue: {exc}")
            end_class_session(session["id"])
            st.session_state.live_class_session = None
            st.session_state.live_class_processor = None
            st.cache_data.clear()
            st.toast("Class ended")
            st.rerun()
    with c3:
        st.caption("Frames are sampled every 4 seconds. Attendance needs two recognitions before PRESENT is saved.")

    st.divider()
    if not is_running:
        st.info("Start a class to open the live camera and automate attendance.")
        _render_detector_status()
        return

    processor = st.session_state.live_class_processor
    _render_live_metrics(processor)

    if webrtc_streamer is None:
        st.error("Live camera requires streamlit-webrtc. Install requirements.txt and restart Streamlit.")
        return

    st.caption("Live Camera")
    webrtc_streamer(
        key=f"live-class-{session['id']}",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=lambda: processor,
        media_stream_constraints={"video": True, "audio": False},
        rtc_configuration=_rtc_configuration(),
        async_processing=True,
    )
    st.caption(
        "If the camera stays at 0:00, allow camera access and configure "
        "TURN_SERVER_URL, TURN_SERVER_USERNAME, and TURN_SERVER_CREDENTIAL in "
        "Streamlit secrets; some networks block direct WebRTC connections."
    )

    if st.button("Refresh Live Stats", width="stretch"):
        st.rerun()

    _render_detector_status()
    _render_session_analytics(session["id"])


def _ensure_live_state():
    if "live_class_session" not in st.session_state:
        st.session_state.live_class_session = None
    if "live_class_processor" not in st.session_state:
        st.session_state.live_class_processor = None


def _rtc_configuration():
    ice_servers = [
        {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]}
    ]
    turn_url = st.secrets.get("TURN_SERVER_URL")
    if turn_url:
        turn_server = {"urls": turn_url}
        turn_username = st.secrets.get("TURN_SERVER_USERNAME")
        turn_credential = st.secrets.get("TURN_SERVER_CREDENTIAL")
        if turn_username:
            turn_server["username"] = turn_username
        if turn_credential:
            turn_server["credential"] = turn_credential
        ice_servers.append(turn_server)

    return {"iceServers": ice_servers}


def _render_live_metrics(processor):
    snap = processor.snapshot()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students Detected", snap["students_detected"])
    c2.metric("Present", f"{snap['present']}/{snap['total']}")
    c3.metric("Absent", snap["absent"])
    c4.metric("Average Engagement", f"{snap['average_engagement']}%")
    if snap.get("last_processed_at"):
        st.caption(f"Last sampled frame: {snap['last_processed_at']}")
    if snap.get("last_error"):
        st.warning(snap["last_error"])


def _render_detector_status():
    detector = ObservableBehaviourDetector()
    with st.expander("Detector availability", expanded=False):
        st.write("Available: face present, student visible/away through existing face recognition.")
        for name, reason in detector.unavailable_features.items():
            st.write(f"Unavailable: {name.replace('_', ' ')} - {reason}")


def _render_session_analytics(session_id):
    render_heading("Classroom Analytics", level=3)
    analytics_rows = get_student_analytics_for_session(session_id)
    events = get_behaviour_events_for_session(session_id)

    if not analytics_rows:
        st.info("Analytics will appear after sampled frames are processed.")
        return

    df = _analytics_df(analytics_rows)
    avg_engagement = round(df["Estimated Engagement %"].mean(), 2) if not df.empty else 0
    high = int((df["Engagement Level"] == "HIGH").sum())
    moderate = int((df["Engagement Level"] == "MODERATE").sum())
    low = int(df["Engagement Level"].isin(["LOW", "VERY LOW"]).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average Engagement", f"{avg_engagement}%")
    c2.metric("Highly Engaged", high)
    c3.metric("Moderately Engaged", moderate)
    c4.metric("Low Engaged", low)

    st.dataframe(df, width="stretch", hide_index=True)

    timeline = _events_df(events)
    if timeline.empty:
        st.info("Behaviour timeline will appear after state changes are detected.")
    else:
        st.caption("Behaviour Timeline")
        st.dataframe(timeline, width="stretch", hide_index=True)


def _analytics_df(rows):
    data = []
    for row in rows:
        student = row.get("students") or {}
        present_duration = int(row.get("present_duration") or 0)
        observed = present_duration + int(row.get("away_duration") or 0)
        attendance_pct = round((present_duration / observed) * 100, 2) if observed else 0
        data.append(
            {
                "Student Name": student.get("name", row.get("student_id")),
                "Attendance %": attendance_pct,
                "Estimated Engagement %": float(row.get("engagement_score") or 0),
                "Engagement Level": row.get("engagement_level") or "VERY LOW",
                "Focused Duration": _format_seconds(row.get("focused_duration")),
                "Distracted Duration": _format_seconds(row.get("distracted_duration")),
                "Phone Usage": _format_seconds(row.get("phone_usage_duration")),
                "Drowsiness": _format_seconds(row.get("drowsy_duration")),
                "Away Time": _format_seconds(row.get("away_duration")),
            }
        )
    return pd.DataFrame(data)


def _events_df(rows):
    data = []
    for row in rows:
        student = row.get("students") or {}
        data.append(
            {
                "Student": student.get("name", row.get("student_id")),
                "Event": row.get("event_type"),
                "Start": row.get("start_time"),
                "End": row.get("end_time") or "Running",
                "Duration": _format_seconds(row.get("duration")),
                "Confidence": row.get("confidence"),
            }
        )
    return pd.DataFrame(data)


def _format_seconds(value):
    seconds = int(value or 0)
    minutes, sec = divmod(seconds, 60)
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"
