import pandas as pd
import streamlit as st

from src.portfolio_attribution import build_fund_pnl_attribution
from ui.pages.fund_explorer import render_fund_detail_dialog


def render_funds_page(context: dict) -> None:
    df = context.get("df")
    color_pnl = context.get("color_pnl")

    st.markdown(
        '<div class="section-title">K12 ? Fon Tablosu</div>',
        unsafe_allow_html=True,
    )
    st.caption("Public demo read-only: add, edit, delete, metadata write and TEFAS refresh actions are not available.")

    detail_options = df["fund_code"].astype(str).tolist()
    detail_name_map = (
        df.set_index("fund_code")["fund_name"].astype(str).to_dict()
        if "fund_name" in df.columns
        else {}
    )

    detail_select_col, detail_action_col = st.columns([2.5, 1])

    with detail_select_col:
        selected_detail_fund = st.selectbox(
            "Tablodan detay icin fon sec",
            detail_options,
            format_func=lambda code: f"{code} - {detail_name_map.get(code, code)}",
            key="k12_detail_selectbox",
        )

    with detail_action_col:
        st.write("")
        st.write("")
        open_detail_dialog = st.button(
            "Detay Penceresini Ac",
            key="k12_open_detail_dialog",
            use_container_width=True,
        )

    if open_detail_dialog:
        selected_dialog_rows = df[df["fund_code"].astype(str) == str(selected_detail_fund)]
        if not selected_dialog_rows.empty:
            render_fund_detail_dialog(selected_dialog_rows.iloc[0])

    pnl_attr_df = build_fund_pnl_attribution(df)[
        ["fund_code", "profit_efficiency"]
    ].copy()

    display_df = df[
        [
            "fund_code",
            "currency",
            "current_value",
            "pnl",
            "return_pct",
            "actual_weight",
            "daily_return_pct",
        ]
    ].copy()

    display_df = display_df.merge(pnl_attr_df, on="fund_code", how="left")
    display_df["profit_efficiency"] = display_df["profit_efficiency"].map(
        lambda value: "N/A" if pd.isna(value) else f"{float(value):.2f}x"
    )

    display_df = display_df.rename(
        columns={
            "fund_code": "Fon",
            "currency": "Kur",
            "current_value": "Guncel Deger",
            "pnl": "K/Z",
            "return_pct": "Getiri %",
            "actual_weight": "Agirlik %",
            "daily_return_pct": "Gunluk %",
            "profit_efficiency": "Kazanc Verimliligi (x)",
        }
    )

    for col in ["Guncel Deger", "K/Z", "Getiri %", "Agirlik %", "Gunluk %"]:
        display_df[col] = display_df[col].map(lambda value: f"{value:,.2f}")

    st.dataframe(
        display_df.style.set_properties(
            subset=["Guncel Deger", "K/Z", "Getiri %", "Agirlik %", "Gunluk %"],
            **{"text-align": "right"},
        ).map(
            color_pnl,
            subset=["K/Z", "Getiri %", "Gunluk %"],
        ),
        column_config={
            "Kazanc Verimliligi (x)": st.column_config.TextColumn(
                "Kazanc Verimliligi (x)",
                help=(
                    "Fonun portfoy toplam kazancina katkisinin, portfoy agirligina orani. "
                    "1.00x uzeri, agirligina kiyasla daha yuksek kazanc katkisini gosterir."
                ),
            ),
        },
        use_container_width=True,
        hide_index=True,
    )
