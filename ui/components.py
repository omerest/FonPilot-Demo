import html

import streamlit as st


def render_section_header(title, subtitle=None):
    st.markdown(f"### {title}")

    if subtitle:
        st.caption(subtitle)


def render_metric_card(label, value, help_text=None):
    st.metric(
        label,
        value,
        help=help_text,
    )


def render_status_badge(label, status):
    status_colors = {
        "OK": "#16a34a",
        "Kontroll\u00fc": "#16a34a",
        "\u0130zlenmeli": "#f59e0b",
        "Kritik": "#dc2626",
        "Eksik": "#dc2626",
    }
    color = status_colors.get(str(status), "#64748b")

    st.markdown(
        f"""
        <span style="
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:2px 8px;
            border-radius:999px;
            border:1px solid {color};
            color:{color};
            font-size:12px;
            font-weight:700;
        ">
            {html.escape(str(label))}: {html.escape(str(status))}
        </span>
        """,
        unsafe_allow_html=True,
    )


def render_info_box(title, body):
    st.info(f"**{title}**\n\n{body}")
