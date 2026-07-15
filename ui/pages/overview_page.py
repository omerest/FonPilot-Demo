import pandas as pd
import plotly.express as px
import streamlit as st

from ui.components import render_section_header
from ui.pages.dashboard_sections import render_portfolio_change_tracker
from ui.pages.fund_explorer import render_fund_detail_dialog


def _delta_class(value) -> str:
    try:
        if float(value) >= 0:
            return "green"
    except Exception:
        pass

    return "red"


def _render_pulse_card(label, value, delta, format_tr_number, format_tr_percent):
    st.markdown(
        f"""
        <div class="k00-pulse-card">
            <div class="k00-pulse-label">{label}</div>
            <div class="k00-pulse-value">{format_tr_number(value)}</div>
            <div class="k00-pulse-delta {_delta_class(delta)}">
                {format_tr_percent(delta)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_risk_appetite_detail(detail: dict):
    st.metric("Mevcut rejim", detail.get("regime", "Veri Yok"))
    st.metric("Risk appetite score", f"%{detail.get('score', 0)}")
    st.caption(
        f"Base skor: {detail.get('base_score', 50)} | "
        f"Ham skor: {detail.get('raw_score', 0)}"
    )

    rows = detail.get("rows", [])
    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
        )

    st.info(detail.get("reason", "Gerekce uretilemedi."))


def _open_risk_appetite_dialog(detail: dict):
    if hasattr(st, "dialog"):
        @st.dialog("Risk-On / Risk-Off Detayi")
        def _dialog():
            _render_risk_appetite_detail(detail)

        _dialog()
        return

    with st.expander("Risk-On / Risk-Off Detayi", expanded=True):
        _render_risk_appetite_detail(detail)


def render_overview_page(context: dict) -> None:
    IS_DEMO_MODE = context.get("IS_DEMO_MODE")
    METADATA_PATH = context.get("METADATA_PATH")
    df = context.get("df")
    market_pulse = context.get("market_pulse")
    risk_appetite = context.get("risk_appetite")
    risk_appetite_detail = context.get("risk_appetite_detail", {})
    total_pnl = context.get("total_pnl")
    daily_pnl_total = context.get("daily_pnl_total")
    total_value = context.get("total_value")
    total_return = context.get("total_return")
    daily_return_total = context.get("daily_return_total")
    tl_funds = context.get("tl_funds")
    usd_funds = context.get("usd_funds")
    positive_count = context.get("positive_count")
    negative_count = context.get("negative_count")
    portfolio_regime = context.get("portfolio_regime")
    exposure_summary = context.get("exposure_summary")
    snapshots_df = context.get("snapshots_df")
    snapshot_changes = context.get("snapshot_changes")
    overall_risk_score = context.get("overall_risk_score")
    overall_risk_level = context.get("overall_risk_level")
    risk_components = context.get("risk_components")
    theme_data = context.get("theme_data")
    attribution_data = context.get("attribution_data")
    awareness_feed = context.get("awareness_feed")
    liquidity_data = context.get("liquidity_data")
    health_data = context.get("health_data")
    data_quality = context.get("data_quality")
    format_try = context.get("format_try")
    format_tr_number = context.get("format_tr_number")
    format_tr_percent = context.get("format_tr_percent")
    color_pnl = context.get("color_pnl")
    run_macro_scenario = context.get("run_macro_scenario")
    calculate_scenario_drivers = context.get("calculate_scenario_drivers")

    render_section_header("K00 · Market Pulse")

    pulse_items = [
        ("USD/TRY", "USDTRY"),
        ("EUR/TRY", "EURTRY"),
        ("Altın", "GOLD"),
        ("DXY", "DXY"),
        ("SP500", "SP500"),
        ("BTC", "BTC"),
        ("QQQM", "QQQM"),
        ("SOXQ", "SOXQ"),
    ]

    pulse_cols = st.columns(9)

    for col, (label, key) in zip(pulse_cols[:8], pulse_items):

        data = market_pulse.get(
            key,
            {"price": 0, "change_pct": 0},
        )

        with col:

            _render_pulse_card(
                label,
                data["price"],
                data["change_pct"],
                format_tr_number,
                format_tr_percent,
            )

    with pulse_cols[8]:

        st.markdown(
            f"""
            <div class="k00-pulse-card">
                <div class="k00-pulse-label">Risk Istahi</div>
                <div class="k00-pulse-value">{risk_appetite["regime"]}</div>
                <div class="k00-pulse-delta">%{risk_appetite["score"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Detay",
            key="k00_risk_appetite_detail",
            use_container_width=True,
        ):
            _open_risk_appetite_dialog(risk_appetite_detail)
    st.caption(
        f"Kaynak: Yahoo Finance | Son Güncelleme: {market_pulse.get('updated_at', 'Veri Yok')}"
    )

    st.divider()

    render_section_header("K01-K06 · Portfolio Overview")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    pnl_class = "green" if total_pnl >= 0 else "red"
    daily_pnl_class = "green" if daily_pnl_total >= 0 else "red"
    daily_return_class = "green" if daily_return_total >= 0 else "red"

    with c1:
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-label">K01 · Güncel Değer</div>
                <div class="fp-value">{format_try(total_value)}</div>
                <div class="fp-sub">
                    Güncel TEFAS değeri
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-label">K02 · Toplam K/Z</div>
                <div class="fp-value {pnl_class}">
                    {format_try(total_pnl)}
                </div>
                <div class="fp-sub">
                    %{total_return:.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-label">K03 · Fon Sayısı</div>
                <div class="fp-value">{len(df)}</div>
                <div class="fp-sub">
                    TL: {tl_funds} · USD: {usd_funds}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-label">K04 · Pozitif Fon</div>
                <div class="fp-value green">{positive_count}</div>
                <div class="fp-sub">
                    Negatif: {negative_count}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c5:
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-label">K05 · Günlük Getiri</div>
                <div class="fp-value {daily_return_class}">
                    %{daily_return_total:.2f}
                </div>
                <div class="fp-sub">
                    Portföy günlük değişim
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c6:
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-label">K06 · Günlük K/Z</div>
                <div class="fp-value {daily_pnl_class}">
                    {format_try(daily_pnl_total)}
                </div>
                <div class="fp-sub">
                    Son fiyat değişimi
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.divider()


    st.markdown("### K14 · Portfolio Health Monitor")

    health_cols = st.columns(6)

    for idx, item in enumerate(health_data):

        col = health_cols[idx % 6]

        with col:

            level = item["level"]

            if level == "Kritik":
                icon = "🔴"
            elif level == "İzlenmeli":
                icon = "🟠"
            else:
                icon = "🟢"

            with st.container(border=True):

                st.markdown(
                    f"**{icon} {item['area']}**"
                )

                st.markdown(
                    f"### {item['status']}"
                )

                st.caption(
                    f"{item['level']} · {item['message']}"
                )

    st.divider()

    st.markdown(
        "<h3 style='color:#9ca3af;'>🛠️ K15 · Data Quality Monitor</h3>",
        unsafe_allow_html=True,
    )
    dq_cols = st.columns(6)

    for idx, item in enumerate(data_quality):

        col = dq_cols[idx % 6]

        with col:

            level = item["level"]

            if level == "Kritik":
                icon = "🔴"
            elif level == "İzlenmeli":
                icon = "🟠"
            else:
                icon = "🟢"

            with st.container(border=True):

                st.markdown(
                    f"**{icon} {item['check']}**"
                )

                st.markdown(
                    f"### {item['status']}"
                )

                st.caption(item["message"])


    st.divider()
