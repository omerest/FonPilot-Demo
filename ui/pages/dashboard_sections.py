import streamlit as st

from ui.components import render_section_header


def _safe_delta_pct(previous, latest):
    try:
        previous_value = float(previous)
        latest_value = float(latest)
    except Exception:
        return "-"

    if previous_value == 0:
        return "-"

    return f"%{((latest_value - previous_value) / abs(previous_value)) * 100:.1f}"


def render_portfolio_change_tracker(snapshot_changes):
    render_section_header("K17 \u00b7 Portfolio Change Tracker")

    if snapshot_changes is None:
        snapshot_changes = []

    if len(snapshot_changes) == 0:
        st.info(
            "Kar\u015f\u0131la\u015ft\u0131rma i\u00e7in en az 2 snapshot gerekli."
        )
        return

    rows = []

    for item in snapshot_changes:
        rows.append(
            {
                "Metrik": item.get("metric", "-"),
                "Onceki": item.get("previous", "-"),
                "Guncel": item.get("latest", "-"),
                "Degisim": f"{item.get('direction', '')} {item.get('delta', '-')}",
                "Degisim %": _safe_delta_pct(
                    item.get("previous"),
                    item.get("latest"),
                ),
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )
