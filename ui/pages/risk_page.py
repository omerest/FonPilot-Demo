import pandas as pd
import streamlit as st

from ui.components import render_section_header


RISK_AUDIT = {
    "currency": {
        "inputs": "currency_exposure_usd, currency_exposure_eur, gold_exposure, foreign_debt_exposure",
        "formula": "USD + EUR*0.7 + Altin*0.8 + Dis Borc*0.8",
        "normalization": "Weighted average exposure values are already percentage-like; clamp to 0-100.",
        "thresholds": "35/55/75 level bands are FonPilot heuristic.",
        "why_bad": "Higher FX-sensitive exposure means TRY portfolio value can move more with currency shocks.",
    },
    "concentration": {
        "inputs": "Top 4 fund weight, technology_exposure, equity_exposure",
        "formula": "Top4Weight*0.7 + (TechnologyWA*0.35 + EquityWA*0.25)*0.8",
        "normalization": "Portfolio weights and exposure percentages are blended then clamped to 0-100.",
        "thresholds": "35/55/75 level bands are FonPilot heuristic.",
        "why_bad": "Higher top-fund or theme clustering reduces effective diversification.",
    },
    "liquidity": {
        "inputs": "sell_value, money_market_exposure",
        "formula": "WeightedSellValue*28 - MoneyMarketWA*0.35 + 25",
        "normalization": "Exit-day proxy is converted to a 0-100 risk score with clamp.",
        "thresholds": "35/55/75 level bands are FonPilot heuristic.",
        "why_bad": "Longer exit value and lower money-market buffer can make stress exits slower.",
    },
    "theme": {
        "inputs": "technology, banking, defense, foreign_equity, gold, commodity, money_market, blockchain exposures",
        "formula": "max(weighted theme exposure) * 1.15",
        "normalization": "Dominant theme percentage is scaled and clamped to 0-100.",
        "thresholds": "35/55/75 level bands are FonPilot heuristic.",
        "why_bad": "A single dominant theme can make apparently diversified funds behave similarly.",
    },
    "volatility": {
        "inputs": "risk_value, equity_exposure, foreign_equity_exposure",
        "formula": "Risk5-7Weight*0.45 + EquityWA*0.35 + ForeignEquityWA*0.25",
        "normalization": "TEFAS risk bucket and equity exposures are blended then clamped to 0-100.",
        "thresholds": "35/55/75 level bands are FonPilot heuristic.",
        "why_bad": "Higher risky-fund and equity exposure increases sensitivity to market swings.",
    },
}


OVERALL_AUDIT = {
    "inputs": "Five component scores: currency, concentration, liquidity, theme, volatility",
    "formula": "currency*0.30 + concentration*0.24 + liquidity*0.14 + theme*0.14 + volatility*0.18",
    "normalization": "Weighted sum is clamped to 0-100.",
    "thresholds": "35/55/75 level bands are FonPilot heuristic.",
    "why_bad": "Higher score means more portfolio risk drivers are elevated at the same time.",
}


def _level_color(level: str) -> str:
    if level in ["Kritik", "Yuksek", "Yüksek"]:
        return "#dc2626"
    if level in ["Izlenmeli", "İzlenmeli", "Orta"]:
        return "#f59e0b"
    return "#16a34a"


def _component_summary(item: dict) -> str:
    return str(item.get("main_metric") or item.get("reason") or "Risk detayi yok.")


def _render_detail_table(rows: list[dict]) -> None:
    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
        )


def _render_liquidity_layers(liquidity_data: dict) -> None:
    st.markdown("#### Likidite katmanlari")
    _render_detail_table(
        [
            {
                "Kart": "Anlik",
                "Input": "sell_value <= 1 olan fonlarin portfolio_weight toplami",
                "Zaman ufku": "T+0 / T+1 cikis proxy",
                "Skor": f"%{liquidity_data.get('instant_ratio', 0)}",
                "Audit": "Likidite korumasi; ayni sinyali risk skoruna dogrudan ikinci kez eklemez.",
            },
            {
                "Kart": "Orta",
                "Input": "1 < sell_value <= 2 olan fonlarin portfolio_weight toplami",
                "Zaman ufku": "T+2 civari cikis proxy",
                "Skor": f"%{liquidity_data.get('medium_ratio', 0)}",
                "Audit": "Anlik ve Yavas katmanlardan ayrisan zaman dilimi.",
            },
            {
                "Kart": "Yavas",
                "Input": "sell_value > 2 olan fonlarin portfolio_weight toplami",
                "Zaman ufku": "T+3 ve uzeri cikis proxy",
                "Skor": f"%{liquidity_data.get('slow_ratio', 0)}",
                "Audit": "Likidite riskini artiran ana cikis yavasligi sinyali.",
            },
            {
                "Kart": "PPF",
                "Input": "money_market_exposure agirlikli ortalamasi",
                "Zaman ufku": "Koruyucu / nakde yakin katman proxy",
                "Skor": f"%{liquidity_data.get('money_market_ratio', 0)}",
                "Audit": "Ayrı risk degil; likidite skorunda riski dusuren koruma boyutu.",
            },
        ]
    )


def _render_risk_detail(
    key: str,
    item: dict,
    awareness_item: dict | None,
    liquidity_data: dict,
) -> None:
    audit = RISK_AUDIT.get(key, OVERALL_AUDIT)

    col_score, col_level = st.columns(2)
    with col_score:
        st.metric("Skor", f"{item.get('score', 0)}/100")
    with col_level:
        st.metric("Seviye", item.get("level", "Veri Yok"))

    st.write(f"**Kisa durum:** {_component_summary(item)}")
    st.write(item.get("reason", "Aciklama yok."))

    st.markdown("#### Skor nasil olustu?")
    _render_detail_table(
        [
            {"Alan": "Kullanilan input", "Detay": audit["inputs"]},
            {"Alan": "Formul", "Detay": audit["formula"]},
            {"Alan": "Normalization", "Detay": audit["normalization"]},
            {"Alan": "Esikler", "Detay": audit["thresholds"]},
            {"Alan": "Skor yukselince neden kotu?", "Detay": audit["why_bad"]},
        ]
    )

    if key == "liquidity":
        st.info(liquidity_data.get("insight", "Likidite insight uretilemedi."))
        _render_liquidity_layers(liquidity_data)

    if awareness_item:
        st.markdown("#### Awareness notu")
        st.caption(
            f"{awareness_item.get('severity', 'Bilgi')} | "
            f"{awareness_item.get('message', '')}"
        )


def _open_risk_detail(
    key: str,
    item: dict,
    awareness_item: dict | None,
    liquidity_data: dict,
) -> None:
    title = item.get("label", "Risk detayi")

    if hasattr(st, "dialog"):
        @st.dialog(f"{title} Detayi")
        def _dialog():
            _render_risk_detail(key, item, awareness_item, liquidity_data)

        _dialog()
        return

    with st.expander(f"{title} Detayi", expanded=True):
        _render_risk_detail(key, item, awareness_item, liquidity_data)


def _render_risk_card(
    key: str,
    item: dict,
    awareness_item: dict | None,
    liquidity_data: dict,
) -> None:
    level = item.get("level", "Veri Yok")
    color = _level_color(level)

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                <div style="font-size:12px; font-weight:850; color:#0f172a;">
                    {item.get('label', 'Risk')}
                </div>
                <div style="font-size:11px; font-weight:800; color:{color};">
                    {level}
                </div>
            </div>
            <div style="font-size:24px; line-height:1.15; font-weight:850; margin-top:6px;">
                {item.get('score', 0)}/100
            </div>
            <div style="font-size:11px; line-height:1.25; color:#64748b; min-height:42px; margin-top:6px;">
                {_component_summary(item)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Detay",
            key=f"k08_risk_detail_{key}",
            use_container_width=True,
        ):
            _open_risk_detail(key, item, awareness_item, liquidity_data)


def _render_overall_detail(overall_score: int, overall_level: str, components: dict) -> None:
    item = {
        "label": "Genel Risk",
        "score": overall_score,
        "level": overall_level,
        "main_metric": "Agirlikli bilesik risk skoru",
        "reason": "Bes risk komponentinin FonPilot agirliklariyla uretilen toplam skoru.",
    }
    _render_risk_detail("overall", item, None, {})

    st.markdown("#### Komponent agirliklari")
    _render_detail_table(
        [
            {"Komponent": "Kur Riski", "Agirlik": "30%", "Skor": components.get("currency", {}).get("score", 0)},
            {"Komponent": "Konsantrasyon", "Agirlik": "24%", "Skor": components.get("concentration", {}).get("score", 0)},
            {"Komponent": "Likidite", "Agirlik": "14%", "Skor": components.get("liquidity", {}).get("score", 0)},
            {"Komponent": "Tema Riski", "Agirlik": "14%", "Skor": components.get("theme", {}).get("score", 0)},
            {"Komponent": "Volatilite", "Agirlik": "18%", "Skor": components.get("volatility", {}).get("score", 0)},
        ]
    )


def _open_overall_detail(overall_score: int, overall_level: str, components: dict) -> None:
    if hasattr(st, "dialog"):
        @st.dialog("Genel Risk Detayi")
        def _dialog():
            _render_overall_detail(overall_score, overall_level, components)

        _dialog()
        return

    with st.expander("Genel Risk Detayi", expanded=True):
        _render_overall_detail(overall_score, overall_level, components)


def render_risk_page(context: dict) -> None:
    overall_risk_score = context.get("overall_risk_score", 0)
    overall_risk_level = context.get("overall_risk_level", "Veri Yok")
    risk_components = context.get("risk_components", {})
    awareness_feed = context.get("awareness_feed", [])
    liquidity_data = context.get("liquidity_data", {})

    render_section_header("K08 · Risk Dashboard")

    component_items = list(risk_components.items())
    awareness_by_key = {
        key: awareness_feed[index]
        for index, (key, _item) in enumerate(component_items)
        if index < len(awareness_feed)
    }

    top_cols = st.columns([1.2, 1, 1, 1, 1, 1])

    with top_cols[0]:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="font-size:12px; font-weight:850; color:#0f172a;">Genel Risk</div>
                <div style="font-size:28px; line-height:1.1; font-weight:900; margin-top:6px;">
                    {overall_risk_score}/100
                </div>
                <div style="font-size:12px; color:{_level_color(overall_risk_level)}; font-weight:850; margin-top:6px;">
                    {overall_risk_level}
                </div>
                <div style="font-size:11px; color:#64748b; margin-top:6px; min-height:42px;">
                    Bes ana risk bileseninin agirlikli toplam skoru.
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Detay",
                key="k08_risk_detail_overall",
                use_container_width=True,
            ):
                _open_overall_detail(
                    overall_risk_score,
                    overall_risk_level,
                    risk_components,
                )

    for col, (key, item) in zip(top_cols[1:], component_items):
        with col:
            _render_risk_card(
                key,
                item,
                awareness_by_key.get(key),
                liquidity_data,
            )

    critical_alerts = [
        item
        for item in awareness_feed
        if item.get("severity") == "Kritik"
    ]

    st.markdown("#### Risk Alerts")
    if critical_alerts:
        for item in critical_alerts:
            st.error(
                f"{item.get('title', 'Risk Alert')}: {item.get('message', '')}"
            )
    else:
        st.caption("Kritik Risk Alert yok. Detaylar ilgili risk kartlarinin icinde.")
