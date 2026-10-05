import streamlit as st


def analytics_kpi_cards(kpis):
    columns = st.columns(3)
    for index, (label, value) in enumerate(kpis.items()):
        with columns[index % 3]:
            st.metric(label, value)


def data_gap_notice(missing_fields):
    if not missing_fields:
        return
    st.info(
        "Some analytics are limited because this database does not currently provide: "
        + ", ".join(missing_fields)
        + "."
    )
