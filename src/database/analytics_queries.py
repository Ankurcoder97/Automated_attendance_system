from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.database.config import supabase


GOOD_THRESHOLD = 85
WARNING_THRESHOLD = 75
SUPPORTED_METHOD_COLUMNS = ("attendance_method", "recognition_method", "method")
STUDENT_COLUMNS = ["student_id", "name", "subject_id", "subject", "subject_code", "section"]
LOG_COLUMNS = [
    "student_id",
    "name",
    "subject_id",
    "subject",
    "subject_code",
    "section",
    "timestamp",
    "date",
    "week",
    "month",
    "is_present",
    "attendance_method",
]


def _safe_execute(query):
    try:
        return query.execute().data or []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_teacher_analytics_source(teacher_id):
    enrollments = _safe_execute(
        supabase.table("subject_students")
        .select("*, students(*), subjects!inner(*)")
        .eq("subjects.teacher_id", teacher_id)
    )
    attendance_logs = _safe_execute(
        supabase.table("attendance_logs")
        .select("*, students(*), subjects!inner(*)")
        .eq("subjects.teacher_id", teacher_id)
    )
    subjects = _safe_execute(
        supabase.table("subjects")
        .select("*")
        .eq("teacher_id", teacher_id)
    )
    return {
        "enrollments": enrollments,
        "attendance_logs": attendance_logs,
        "subjects": subjects,
    }


def build_teacher_analytics(source):
    enrollments = source.get("enrollments", [])
    logs = source.get("attendance_logs", [])
    subjects = source.get("subjects", [])

    students_df = _build_students_df(enrollments)
    subjects_df = pd.DataFrame(subjects)
    logs_df = _build_logs_df(logs)
    student_summary = _build_student_summary(students_df, logs_df)
    subject_summary = _build_subject_summary(subjects_df, logs_df)

    return {
        "students": students_df,
        "subjects": subjects_df,
        "logs": logs_df,
        "student_summary": student_summary,
        "subject_summary": subject_summary,
        "missing": _missing_fields(logs_df),
    }


def _build_students_df(enrollments):
    rows = []
    seen = set()
    for item in enrollments:
        student = item.get("students") or {}
        subject = item.get("subjects") or {}
        key = (student.get("student_id"), subject.get("subject_id"))
        if key in seen or not student:
            continue
        seen.add(key)
        rows.append(
            {
                "student_id": student.get("student_id"),
                "name": student.get("name", "Unknown"),
                "subject_id": subject.get("subject_id"),
                "subject": subject.get("name", "Unknown"),
                "subject_code": subject.get("subject_code", ""),
                "section": subject.get("section", ""),
            }
        )
    return pd.DataFrame(rows, columns=STUDENT_COLUMNS)


def _build_logs_df(logs):
    rows = []
    for item in logs:
        student = item.get("students") or {}
        subject = item.get("subjects") or {}
        method = next((item.get(col) for col in SUPPORTED_METHOD_COLUMNS if item.get(col)), None)
        ts = pd.to_datetime(item.get("timestamp"), errors="coerce")
        rows.append(
            {
                "student_id": item.get("student_id"),
                "name": student.get("name", "Unknown"),
                "subject_id": item.get("subject_id"),
                "subject": subject.get("name", "Unknown"),
                "subject_code": subject.get("subject_code", ""),
                "section": subject.get("section", ""),
                "timestamp": ts,
                "date": ts.date() if pd.notna(ts) else None,
                "week": ts.to_period("W").start_time.date() if pd.notna(ts) else None,
                "month": ts.to_period("M").start_time.date() if pd.notna(ts) else None,
                "is_present": bool(item.get("is_present")),
                "attendance_method": method,
            }
        )
    df = pd.DataFrame(rows, columns=LOG_COLUMNS)
    if not df.empty:
        df = df.sort_values("timestamp")
    return df


def _build_student_summary(students_df, logs_df):
    if students_df.empty:
        return pd.DataFrame()

    base = (
        students_df[["student_id", "name"]]
        .drop_duplicates("student_id")
        .sort_values("name")
        .reset_index(drop=True)
    )

    if logs_df.empty:
        base["total_classes"] = 0
        base["present"] = 0
        base["absent"] = 0
        base["late"] = 0
        base["attendance_percentage"] = 0.0
        base["attendance_trend"] = "No data"
        base["last_seen"] = None
        base["first_seen"] = None
        base["status"] = "No Data"
        base["consecutive_absences"] = 0
        base["risk_reason"] = "No attendance records"
        return base

    grouped = logs_df.groupby("student_id", dropna=False)
    summary = grouped.agg(
        total_classes=("is_present", "count"),
        present=("is_present", "sum"),
        last_seen=("timestamp", "max"),
        first_seen=("timestamp", "min"),
    ).reset_index()
    summary["present"] = summary["present"].astype(int)
    summary["absent"] = summary["total_classes"] - summary["present"]
    summary["late"] = 0
    summary["attendance_percentage"] = summary.apply(
        lambda row: round((row["present"] / row["total_classes"]) * 100, 2)
        if row["total_classes"]
        else 0.0,
        axis=1,
    )
    summary["attendance_trend"] = summary["student_id"].apply(lambda sid: _student_trend(logs_df, sid))
    summary["status"] = summary["attendance_percentage"].apply(classify_status)
    summary["consecutive_absences"] = summary["student_id"].apply(
        lambda sid: _consecutive_absences(logs_df, sid)
    )
    summary["risk_reason"] = summary.apply(_risk_reason, axis=1)

    merged = base.merge(summary, on="student_id", how="left")
    fill_values = {
        "total_classes": 0,
        "present": 0,
        "absent": 0,
        "late": 0,
        "attendance_percentage": 0.0,
        "attendance_trend": "No data",
        "status": "No Data",
        "consecutive_absences": 0,
        "risk_reason": "No attendance records",
    }
    return merged.fillna(fill_values)


def _build_subject_summary(subjects_df, logs_df):
    if subjects_df.empty:
        return pd.DataFrame()
    base = subjects_df[["subject_id", "name", "subject_code", "section"]].rename(
        columns={"name": "subject"}
    )
    if logs_df.empty:
        base["total_records"] = 0
        base["present"] = 0
        base["absent"] = 0
        base["attendance_percentage"] = 0.0
        return base

    summary = logs_df.groupby("subject_id").agg(
        total_records=("is_present", "count"),
        present=("is_present", "sum"),
    ).reset_index()
    summary["present"] = summary["present"].astype(int)
    summary["absent"] = summary["total_records"] - summary["present"]
    summary["attendance_percentage"] = summary.apply(
        lambda row: round((row["present"] / row["total_records"]) * 100, 2)
        if row["total_records"]
        else 0.0,
        axis=1,
    )
    return base.merge(summary, on="subject_id", how="left").fillna(
        {"total_records": 0, "present": 0, "absent": 0, "attendance_percentage": 0.0}
    )


def classify_status(percentage):
    if percentage >= GOOD_THRESHOLD:
        return "Good"
    if percentage >= WARNING_THRESHOLD:
        return "Warning"
    return "At Risk"


def _student_trend(logs_df, student_id):
    student_logs = logs_df[logs_df["student_id"] == student_id].sort_values("timestamp")
    if len(student_logs) < 4:
        return "Not enough data"
    recent = student_logs.tail(5)["is_present"].mean()
    previous = student_logs.iloc[:-5].tail(5)["is_present"].mean()
    if pd.isna(previous):
        previous = student_logs.head(max(len(student_logs) - 1, 1))["is_present"].mean()
    delta = recent - previous
    if delta > 0.05:
        return "Improving"
    if delta < -0.05:
        return "Declining"
    return "Stable"


def _consecutive_absences(logs_df, student_id):
    student_logs = logs_df[logs_df["student_id"] == student_id].sort_values("timestamp")
    count = 0
    for value in reversed(student_logs["is_present"].tolist()):
        if value:
            break
        count += 1
    return count


def _risk_reason(row):
    reasons = []
    if row["attendance_percentage"] < WARNING_THRESHOLD:
        reasons.append("Attendance below 75%")
    if row["consecutive_absences"] >= 2:
        reasons.append(f"{int(row['consecutive_absences'])} consecutive absences")
    if row["attendance_trend"] == "Declining":
        reasons.append("Declining trend")
    return ", ".join(reasons) if reasons else "Healthy"


def apply_analytics_filters(logs_df, students_df, filters):
    filtered_logs = logs_df.copy()
    filtered_students = students_df.copy()

    if filters.get("student_id") != "All":
        sid = filters["student_id"]
        filtered_logs = filtered_logs[filtered_logs["student_id"] == sid]
        filtered_students = filtered_students[filtered_students["student_id"] == sid]

    if filters.get("subject_id") != "All":
        subject_id = filters["subject_id"]
        filtered_logs = filtered_logs[filtered_logs["subject_id"] == subject_id]
        filtered_students = filtered_students[filtered_students["subject_id"] == subject_id]

    if filters.get("section") != "All":
        section = filters["section"]
        filtered_logs = filtered_logs[filtered_logs["section"] == section]
        filtered_students = filtered_students[filtered_students["section"] == section]

    date_range = filters.get("date_range")
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
        if isinstance(start_date, date) and isinstance(end_date, date):
            filtered_logs = filtered_logs[
                (filtered_logs["date"] >= start_date) & (filtered_logs["date"] <= end_date)
            ]

    return filtered_logs, filtered_students


def dashboard_kpis(students_df, logs_df, summary_df):
    today = date.today()
    today_logs = logs_df[logs_df["date"] == today] if not logs_df.empty else pd.DataFrame()
    present_today = int(today_logs["is_present"].sum()) if not today_logs.empty else 0
    absent_today = int((~today_logs["is_present"]).sum()) if not today_logs.empty else 0
    total_records = len(logs_df)
    present_records = int(logs_df["is_present"].sum()) if total_records else 0
    attendance_pct = round((present_records / total_records) * 100, 2) if total_records else 0.0
    at_risk = int((summary_df["status"] == "At Risk").sum()) if not summary_df.empty else 0
    return {
        "Total Students": int(students_df["student_id"].nunique()) if not students_df.empty else 0,
        "Present Today": present_today,
        "Absent Today": absent_today,
        "Attendance Percentage": f"{attendance_pct}%",
        "Late Students": 0,
        "At-Risk Students": at_risk,
    }


def _missing_fields(logs_df):
    missing = []
    if logs_df.empty:
        missing.append("attendance_logs records")
    elif "attendance_method" not in logs_df.columns or logs_df["attendance_method"].dropna().empty:
        missing.append("attendance_logs.attendance_method")
    missing.append("late arrival field")
    return missing
