import pandas as pd
import streamlit as st


def attendance_trend_charts(logs_df):
    if logs_df.empty:
        st.info("Data not available: attendance_logs records are required for trends.")
        return

    daily = _trend_frame(logs_df, "date", "Daily Attendance %")
    weekly = _trend_frame(logs_df, "week", "Weekly Attendance %")
    monthly = _trend_frame(logs_df, "month", "Monthly Attendance %")

    tab_daily, tab_weekly, tab_monthly = st.tabs(["Daily", "Weekly", "Monthly"])
    with tab_daily:
        _line_chart(daily, "date", "Daily Attendance %")
    with tab_weekly:
        _line_chart(weekly, "week", "Weekly Attendance %")
    with tab_monthly:
        _line_chart(monthly, "month", "Monthly Attendance %")


def attendance_distribution_charts(logs_df):
    if logs_df.empty:
        st.info("Data not available: attendance_logs records are required for distributions.")
        return

    c1, c2 = st.columns(2)
    status_counts = (
        logs_df.assign(Status=logs_df["is_present"].map({True: "Present", False: "Absent"}))
        .groupby("Status")
        .size()
        .reset_index(name="Count")
    )
    with c1:
        st.caption("Present vs Absent")
        st.bar_chart(status_counts, x="Status", y="Count", color="Status")

    method_logs = logs_df.copy()
    method_logs["Attendance Method"] = (
        method_logs["attendance_method"]
        .fillna("unknown")
        .replace(
            {
                "face": "Face",
                "voice": "Voice",
                "live_face": "Live face",
                "unknown": "Unknown / legacy",
            }
        )
    )
    with c2:
        st.caption("Attendance Method")
        method_counts = (
            method_logs.groupby("Attendance Method")
            .size()
            .reset_index(name="Count")
        )
        st.bar_chart(method_counts, x="Attendance Method", y="Count", color="Attendance Method")


def subject_attendance_chart(subject_summary):
    if subject_summary.empty:
        st.info("Data not available: subjects are required for subject-wise analytics.")
        return
    chart_df = subject_summary[["subject", "attendance_percentage"]].sort_values(
        "attendance_percentage", ascending=True
    )
    st.bar_chart(chart_df, x="subject", y="attendance_percentage")


def _trend_frame(logs_df, period_col, label):
    trend = (
        logs_df.dropna(subset=[period_col])
        .groupby(period_col)
        .agg(records=("is_present", "count"), present=("is_present", "sum"))
        .reset_index()
    )
    if trend.empty:
        return trend
    trend[label] = (trend["present"] / trend["records"] * 100).round(2)
    return trend


def _line_chart(df, x_col, y_col):
    if df.empty:
        st.info("No records found for this period.")
        return
    st.line_chart(df, x=x_col, y=y_col)
