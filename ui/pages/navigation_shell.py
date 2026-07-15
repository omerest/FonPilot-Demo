import streamlit as st


NAV_ITEMS = [
    "Overview",
    "Risk",
    "Exposure",
    "Macro",
    "Funds",
    "History",
]


def render_main_navigation(default: str = "Overview", is_demo_mode: bool = False) -> str:
    if default not in NAV_ITEMS:
        default = "Overview"

    with st.sidebar:
        st.markdown("### FonPilot")
        selected_page = st.radio(
            "Navigation",
            NAV_ITEMS,
            index=NAV_ITEMS.index(default),
            key="main_navigation_page",
            label_visibility="collapsed",
        )

        st.caption("Demo read-only" if is_demo_mode else "Local mode")

    return selected_page
