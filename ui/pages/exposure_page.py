import pandas as pd
import plotly.express as px
import streamlit as st

from src.portfolio_attribution import build_fund_pnl_attribution
from ui.components import render_section_header
from ui.pages.dashboard_sections import render_portfolio_change_tracker
from ui.pages.fund_explorer import render_fund_detail_dialog


def render_exposure_page(context: dict) -> None:
    IS_DEMO_MODE = context.get("IS_DEMO_MODE")
    METADATA_PATH = context.get("METADATA_PATH")
    df = context.get("df")
    market_pulse = context.get("market_pulse")
    risk_appetite = context.get("risk_appetite")
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

    render_section_header("K11 · Exposure Engine")

    exp_cols = st.columns(8)

    for col, (label, data) in zip(exp_cols, exposure_summary.items()):

        value = data["value"]
        level = data["level"]

        if value >= 60:
            delta_color = "inverse"
        elif value >= 30:
            delta_color = "off"
        else:
            delta_color = "normal"

        with col:
            st.metric(
                label,
                f"%{value}",
                level,
                delta_color=delta_color,
            )

    st.divider()


    left, right = st.columns([1, 1])

    with left:

        st.markdown(
            '<div class="section-title">K09 · Portföy Dağılımı</div>',
            unsafe_allow_html=True,
        )

        fig = px.pie(
            df,
            names="fund_code",
            values="current_value",
            hole=0.55,
        )

        fig.update_layout(
            height=420,
            margin=dict(l=0, r=0, t=0, b=0),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with right:

        st.markdown(
            '<div class="section-title">K10 · Fon Bazlı K/Z</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Katki %, fonun net portfoy K/Z sonucuna katkisini gosterir. "
            "Pozitif ve negatif fonlar birlikte bulundugunda katkilarin mutlak toplami %100'u asabilir."
        )

        pnl_attr_df = build_fund_pnl_attribution(df)
        pnl_attr_df["pnl_label"] = pnl_attr_df["pnl"].apply(format_try)
        pnl_attr_df["bar_color"] = pnl_attr_df["pnl"].apply(
            lambda value: "Pozitif" if value > 0 else "Negatif" if value < 0 else "Notr"
        )
        pnl_attr_df["text_label"] = (
            "Katki: "
            + pnl_attr_df["portfolio_pnl_contribution_pct"].map("{:+.1f}%".format)
            + "<br>Fon Getirisi: "
            + pnl_attr_df["fund_return_pct"].map("{:+.1f}%".format)
            + "<br>K/Z: "
            + pnl_attr_df["pnl_label"]
        )

        fig = px.bar(
            pnl_attr_df,
            x="fund_code",
            y="portfolio_pnl_contribution_pct",
            text="text_label",
            color="bar_color",
            color_discrete_map={
                "Pozitif": "#16a34a",
                "Negatif": "#dc2626",
                "Notr": "#64748b",
            },
            labels={
                "fund_code": "Fon",
                "portfolio_pnl_contribution_pct": "Toplam K/Z Katki %",
            },
        )

        fig.update_traces(
            textposition="outside",
            hovertemplate="%{text}<extra></extra>",
        )

        fig.update_layout(
            height=420,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            yaxis_title="Toplam K/Z Katki %",
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.divider()


    st.markdown("### K07A · Theme Concentration Engine")

    theme_cols = st.columns(4)

    for idx, item in enumerate(theme_data):

        col = theme_cols[idx % 4]

        with col:

            risk_effect = item["risk_effect"]

            if risk_effect == "Yüksek":
                delta_color = "inverse"
            elif risk_effect == "Orta":
                delta_color = "off"
            elif risk_effect == "Koruyucu":
                delta_color = "normal"
            else:
                delta_color = "normal"

            st.metric(
                item["theme"],
                f"%{item['value']}",
                risk_effect,
                delta_color=delta_color,
            )



    st.markdown(
        "<h3 style='color:#a855f7;'>🧠 K10B · Performance Attribution Engine</h3>",
        unsafe_allow_html=True,
    )

    attr_left, attr_right = st.columns([0.9, 1.3])

    with attr_left:

        attr_df = pd.DataFrame(
            attribution_data["items"]
        )

        st.bar_chart(
            attr_df.set_index("label"),
            height=240,
        )

    with attr_right:

        st.caption("Attribution Insight")
        st.info(attribution_data["insight"])

        compact_cols = st.columns(len(attribution_data["items"]))

        for col, item in zip(compact_cols, attribution_data["items"]):
            with col:
                st.metric(
                    item["label"],
                    f"%{item['weight']}",
                )

    st.divider()
