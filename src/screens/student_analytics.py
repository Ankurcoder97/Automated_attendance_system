import pandas as pd
import streamlit as st

from src.components.analytics_cards import analytics_kpi_cards, data_gap_notice
from src.components.analytics_charts import (
    attendance_distribution_charts,
    attendance_trend_charts,
    subject_attendance_chart,
)
from src.database.analytics_queries import (
    apply_analytics_filters,
    build_teacher_analytics,
    dashboard_kpis,
    get_teacher_analytics_source,
)
from src.ui.base_layout import render_heading


def student_analytics_screen(teacher_id):
    render_heading("Student Analytics", level=2)

    source = get_teacher_analytics_source(teacher_id)
    analytics = build_teacher_analytics(source)
    logs_df = analytics["logs"]
    students_df = analytics["students"]
    summary_df = analytics["student_summary"]
    subject_summary = analytics["subject_summary"]

    data_gap_notice(analytics["missing"])

    if students_df.empty:
        st.warning("Data not available: no enrolled students found for your subjects.")
        return

    filters = _render_filters(students_df, logs_df, summary_df)
    filtered_logs, filtered_students = apply_analytics_filters(logs_df, students_df, filters)
    filtered_summary = _filter_summary(summary_df, filtered_students, filters)

    analytics_kpi_cards(dashboard_kpis(filtered_students, filtered_logs, filtered_summary))
    st.divider()

    overview_tab, students_tab, risk_tab, subjects_tab, classroom_tab, export_tab = st.tabs(
        [
            "Overview",
            "Students",
            "At Risk",
            "Subjects",
            "Classroom",
            "Export",
        ]
    )

    with overview_tab:
        render_heading("Attendance Overview", level=3)
        attendance_trend_charts(filtered_logs)
        attendance_distribution_charts(filtered_logs)

    with students_tab:
        _student_table(filtered_summary)
        _individual_student_detail(filtered_summary, filtered_logs, students_df)

    with risk_tab:
        _risk_section(filtered_summary)

    with subjects_tab:
        _subject_section(subject_summary, filtered_logs)

    with classroom_tab:
        _classroom_section(filtered_logs)

    with export_tab:
        _export_section(filtered_logs, filtered_summary)


def _render_filters(students_df, logs_df, summary_df):
    with st.container(border=True):
        st.caption("Filters")
        c1, c2, c3 = st.columns(3)

        student_options = {"All": "All"}
        for row in students_df[["student_id", "name"]].drop_duplicates().sort_values("name").to_dict("records"):
            student_options[f"{row['name']} ({row['student_id']})"] = row["student_id"]

        subject_options = {"All": "All"}
        for row in students_df[["subject_id", "subject", "subject_code"]].drop_duplicates().sort_values("subject").to_dict("records"):
            subject_options[f"{row['subject']} ({row['subject_code']})"] = row["subject_id"]

        with c1:
            student_id = student_options[
                st.selectbox("Student", list(student_options.keys()))
            ]
            status = st.selectbox("Attendance status", ["All", "Good", "Warning", "At Risk", "No Data"])
        with c2:
            subject_id = subject_options[
                st.selectbox("Subject", list(subject_options.keys()))
            ]
            sections = ["All"] + sorted([s for s in students_df["section"].dropna().unique().tolist() if s])
            section = st.selectbox("Section", sections)
        with c3:
            if logs_df.empty or logs_df["date"].dropna().empty:
                date_range = None
                st.date_input("Date range", value=None, disabled=True)
            else:
                min_date = logs_df["date"].dropna().min()
                max_date = logs_df["date"].dropna().max()
                date_range = st.date_input("Date range", value=(min_date, max_date))

        return {
            "student_id": student_id,
            "subject_id": subject_id,
            "section": section,
            "status": status,
            "date_range": date_range,
        }


def _filter_summary(summary_df, filtered_students, filters):
    if summary_df.empty:
        return summary_df
    allowed_students = filtered_students["student_id"].dropna().unique().tolist()
    filtered = summary_df[summary_df["student_id"].isin(allowed_students)]
    if filters.get("status") != "All":
        filtered = filtered[filtered["status"] == filters["status"]]
    return filtered


def _student_table(summary_df):
    render_heading("Student Performance Analytics", level=3)
    query = st.text_input("Search students", placeholder="Search by name or student ID")
    display = summary_df.copy()
    if query:
        q = query.lower()
        display = display[
            display["name"].astype(str).str.lower().str.contains(q)
            | display["student_id"].astype(str).str.lower().str.contains(q)
        ]

    columns = {
        "student_id": "Student ID",
        "name": "Name",
        "present": "Present",
        "absent": "Absent",
        "late": "Late",
        "attendance_percentage": "Attendance %",
        "status": "Status",
        "last_seen": "Last Seen",
    }
    st.dataframe(
        display[list(columns.keys())].rename(columns=columns),
        width="stretch",
        hide_index=True,
    )


def _individual_student_detail(summary_df, logs_df, students_df):
    render_heading("Individual Student Analytics", level=3)
    if summary_df.empty:
        st.info("Select filters with at least one student to view individual analytics.")
        return

    options = {
        f"{row['name']} ({row['student_id']})": row["student_id"]
        for row in summary_df.sort_values("name").to_dict("records")
    }
    selected_label = st.selectbox("Student profile", list(options.keys()))
    student_id = options[selected_label]
    student = summary_df[summary_df["student_id"] == student_id].iloc[0]
    student_logs = logs_df[logs_df["student_id"] == student_id].sort_values("timestamp")
    enrollments = students_df[students_df["student_id"] == student_id]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Attendance", f"{student['attendance_percentage']}%")
    c2.metric("Present", int(student["present"]))
    c3.metric("Absent", int(student["absent"]))
    c4.metric("Risk Level", student["status"])

    profile = {
        "Student ID": student["student_id"],
        "Name": student["name"],
        "Subjects": ", ".join(enrollments["subject"].dropna().unique().tolist()) or "N/A",
        "First Attendance": _format_ts(student.get("first_seen")),
        "Last Attendance": _format_ts(student.get("last_seen")),
        "Consecutive Absences": int(student["consecutive_absences"]),
        "Attendance Trend": student["attendance_trend"],
    }
    st.dataframe(pd.DataFrame(profile.items(), columns=["Field", "Value"]), hide_index=True, width="stretch")

    if student_logs.empty:
        st.info("Data not available: this student has no attendance records yet.")
        return

    c1, c2 = st.columns(2)
    with c1:
        weekly = _student_period_chart(student_logs, "week", "Weekly Attendance %")
        st.line_chart(weekly, x="week", y="Weekly Attendance %") if not weekly.empty else st.info("No weekly data.")
    with c2:
        monthly = _student_period_chart(student_logs, "month", "Monthly Attendance %")
        st.line_chart(monthly, x="month", y="Monthly Attendance %") if not monthly.empty else st.info("No monthly data.")

    subject = (
        student_logs.groupby("subject")
        .agg(Total=("is_present", "count"), Present=("is_present", "sum"))
        .reset_index()
    )
    subject["Attendance %"] = (subject["Present"] / subject["Total"] * 100).round(2)
    st.caption("Subject-wise attendance")
    st.dataframe(subject, hide_index=True, width="stretch")

    recent = student_logs.tail(10).copy()
    recent["Status"] = recent["is_present"].map({True: "Present", False: "Absent"})
    st.caption("Recent attendance history")
    st.dataframe(
        recent[["timestamp", "subject", "Status", "attendance_method"]].rename(
            columns={"timestamp": "Time", "subject": "Subject", "attendance_method": "Method"}
        ),
        hide_index=True,
        width="stretch",
    )


def _risk_section(summary_df):
    render_heading("At Risk Students", level=3)
    if summary_df.empty:
        st.info("Data not available: student attendance records are required for risk analytics.")
        return
    risk = summary_df[
        (summary_df["status"] == "At Risk")
        | (summary_df["consecutive_absences"] >= 2)
        | (summary_df["attendance_trend"] == "Declining")
    ].copy()
    if risk.empty:
        st.success("No at-risk students found with the current filters.")
        return
    st.dataframe(
        risk[["name", "attendance_percentage", "consecutive_absences", "risk_reason"]].rename(
            columns={
                "name": "Student",
                "attendance_percentage": "Attendance %",
                "consecutive_absences": "Consecutive Absences",
                "risk_reason": "Risk Reason",
            }
        ),
        hide_index=True,
        width="stretch",
    )


def _subject_section(subject_summary, logs_df):
    render_heading("Subject-wise Analytics", level=3)
    subject_attendance_chart(subject_summary)
    if subject_summary.empty:
        return
    st.dataframe(subject_summary, hide_index=True, width="stretch")

    low = logs_df.groupby(["subject", "student_id", "name"]).agg(
        total=("is_present", "count"), present=("is_present", "sum")
    ).reset_index() if not logs_df.empty else pd.DataFrame()
    if not low.empty:
        low["attendance_percentage"] = (low["present"] / low["total"] * 100).round(2)
        low = low[low["attendance_percentage"] < 75]
        st.caption("Students with low subject attendance")
        st.dataframe(low, hide_index=True, width="stretch")


def _classroom_section(logs_df):
    render_heading("Classroom Analytics", level=3)
    if logs_df.empty:
        st.info("Data not available: attendance_logs records are required for classroom analytics.")
        return
    today = pd.Timestamp.today().date()
    today_logs = logs_df[logs_df["date"] == today]
    avg = round(logs_df["is_present"].mean() * 100, 2)
    daily = logs_df.groupby("date").agg(total=("is_present", "count"), present=("is_present", "sum")).reset_index()
    daily["attendance_percentage"] = (daily["present"] / daily["total"] * 100).round(2)

    c1, c2, c3 = st.columns(3)
    c1.metric("Today's Attendance", int(today_logs["is_present"].sum()) if not today_logs.empty else 0)
    c2.metric("Average Class Attendance", f"{avg}%")
    c3.metric("Attendance Records", len(logs_df))

    if not daily.empty:
        peak = daily.sort_values("attendance_percentage", ascending=False).head(1).iloc[0]
        low = daily.sort_values("attendance_percentage", ascending=True).head(1).iloc[0]
        st.write(f"Peak attendance day: {peak['date']} ({peak['attendance_percentage']}%)")
        st.write(f"Lowest attendance day: {low['date']} ({low['attendance_percentage']}%)")
        st.line_chart(daily, x="date", y="attendance_percentage")


def _export_section(logs_df, summary_df):
    render_heading("Export", level=3)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Export attendance CSV",
            data=logs_df.to_csv(index=False).encode("utf-8"),
            file_name="attendance_records.csv",
            mime="text/csv",
            width="stretch",
        )
    with c2:
        st.download_button(
            "Export student analytics CSV",
            data=summary_df.to_csv(index=False).encode("utf-8"),
            file_name="student_analytics.csv",
            mime="text/csv",
            width="stretch",
        )


def _student_period_chart(student_logs, period_col, label):
    data = student_logs.dropna(subset=[period_col]).groupby(period_col).agg(
        total=("is_present", "count"), present=("is_present", "sum")
    ).reset_index()
    if data.empty:
        return data
    data[label] = (data["present"] / data["total"] * 100).round(2)
    return data


def _format_ts(value):
    if pd.isna(value) or value is None:
        return "N/A"
    return pd.to_datetime(value).strftime("%Y-%m-%d %I:%M %p")
