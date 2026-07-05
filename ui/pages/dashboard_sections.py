import streamlit as st

from ui.components import render_section_header


def render_portfolio_change_tracker(snapshot_changes):
    render_section_header("K17 \u00b7 Portfolio Change Tracker")

    if len(snapshot_changes) == 0:
        st.info(
            "Kar\u015f\u0131la\u015ft\u0131rma i\u00e7in en az 2 snapshot gerekli."
        )
        return

    change_cols = st.columns(4)

    for idx, item in enumerate(snapshot_changes):
        col = change_cols[idx % 4]

        with col:
            delta_text = (
                f"{item['direction']} {item['delta']}"
            )

            delta_color = (
                "normal"
                if item["delta"] >= 0
                else "inverse"
            )

            st.metric(
                item["metric"],
                item["latest"],
                delta=delta_text,
                delta_color=delta_color,
            )
