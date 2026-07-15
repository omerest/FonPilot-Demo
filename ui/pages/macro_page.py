import streamlit as st

from src.risk_engine import SCENARIO_CONFIG
from ui.components import render_section_header


def _render_regime_detail(portfolio_regime: dict) -> None:
    st.metric("Skor", portfolio_regime.get("score", 0))
    st.metric("Rejim", portfolio_regime.get("regime_name", "Veri Yok"))
    st.write("**Skoru yukari ceken faktorler**")
    st.write(", ".join(portfolio_regime.get("positive_factors", [])) or "Veri yok")
    st.write("**Skoru asagi ceken / dengeleyen faktorler**")
    st.write(", ".join(portfolio_regime.get("negative_factors", [])) or "Veri yok")
    st.caption(portfolio_regime.get("definition", ""))
    st.info(portfolio_regime.get("comment", ""))


def _open_regime_dialog(portfolio_regime: dict) -> None:
    if hasattr(st, "dialog"):
        @st.dialog("Portfolio Regime Detayi")
        def _dialog():
            _render_regime_detail(portfolio_regime)

        _dialog()
        return

    with st.expander("Portfolio Regime Detayi", expanded=True):
        _render_regime_detail(portfolio_regime)


def render_macro_page(context: dict) -> None:
    portfolio_regime = context.get("portfolio_regime", {})
    tcmb_policy_rate = context.get("tcmb_policy_rate", {})
    run_macro_scenario = context.get("run_macro_scenario")
    calculate_scenario_drivers = context.get("calculate_scenario_drivers")

    render_section_header("Portfolio Regime")

    regime_cols = st.columns(4)

    with regime_cols[0]:
        st.metric("Rejim", portfolio_regime.get("regime_name", "Veri Yok"))

    with regime_cols[1]:
        st.metric("Skor", portfolio_regime.get("score", 0))

    with regime_cols[2]:
        st.metric("Ana Surucu", portfolio_regime.get("driver", "Veri Yok"))

    with regime_cols[3]:
        st.metric(
            "Makro Hassasiyet",
            portfolio_regime.get("macro_sensitivity", "Veri Yok"),
        )

    if st.button("Rejim Detayi", key="portfolio_regime_detail"):
        _open_regime_dialog(portfolio_regime)

    st.divider()

    render_section_header("K16 · Macro Scenario Simulator")

    rate_value = tcmb_policy_rate.get("value")
    rate_text = f"%{rate_value:.2f}" if rate_value is not None else "Veri alinamadi"
    st.caption(
        f"TCMB Politika Faizi: {rate_text} | "
        f"Kaynak: {tcmb_policy_rate.get('source', 'TCMB EVDS')} | "
        f"{tcmb_policy_rate.get('message', '')}"
    )

    scenario_inputs = {}
    scenario_names = list(SCENARIO_CONFIG.keys())
    input_cols = st.columns(3)

    for idx, scenario_name in enumerate(scenario_names):
        config = SCENARIO_CONFIG[scenario_name]
        default_value = -5.0 if scenario_name == "TCMB Policy Rate Forecast" else 10.0

        with input_cols[idx % 3]:
            scenario_inputs[scenario_name] = st.number_input(
                config["label"],
                min_value=-100.0,
                max_value=100.0,
                value=default_value,
                step=0.25,
                format="%.2f",
                key=f"macro_input_{scenario_name}",
                help=f"Birim: {config['unit']}",
            )

    selected_scenario = st.selectbox(
        "K16A detay senaryosu",
        scenario_names,
        key="macro_scenario_select",
    )
    shock_value = scenario_inputs[selected_scenario]

    scenario_result = run_macro_scenario(
        selected_scenario,
        shock_value,
    )

    scenario_drivers_df = calculate_scenario_drivers(
        selected_scenario,
        shock_value,
    )

    sr1, sr2 = st.columns(2)

    with sr1:
        st.metric(
            "Tahmini Etki (%)",
            f"%{scenario_result['estimated_impact_pct']}",
            f"Exposure %{scenario_result.get('relevant_exposure', 0)}",
        )

    with sr2:
        st.metric(
            "Tahmini Etki (TL)",
            f"{scenario_result['estimated_impact_tl']:,.0f} TL",
            f"Sensitivity {scenario_result.get('sensitivity', 0)}",
        )

    st.caption(scenario_result["comment"])

    st.markdown("#### K16A · Scenario Driver Breakdown")
    show_all_drivers = st.checkbox(
        "Tum fonlari goster",
        value=False,
        key="show_all_scenario_drivers",
    )

    if len(scenario_drivers_df) == 0:
        st.info("Senaryo driver verisi olusmadi.")
    else:
        display_df = scenario_drivers_df.copy()

        if not show_all_drivers:
            display_df = display_df.head(5)

        for column in [
            "scenario_shock",
            "relevant_exposure",
            "sensitivity",
            "estimated_effect_pct",
            "estimated_effect_tl",
        ]:
            display_df[column] = display_df[column].round(2)

        st.dataframe(
            display_df.rename(
                columns={
                    "fund_code": "Fon",
                    "scenario_shock": "Scenario Shock",
                    "relevant_exposure": "Relevant Exposure %",
                    "sensitivity": "Sensitivity",
                    "estimated_effect_pct": "Etki %",
                    "estimated_effect_tl": "Etki TL",
                    "theme_primary": "Tema",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
