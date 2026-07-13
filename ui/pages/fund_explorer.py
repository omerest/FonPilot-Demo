import pandas as pd
import streamlit as st


def _to_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _to_int_label(value) -> str:
    try:
        if pd.isna(value):
            return "Veri Yok"
        return str(int(float(value)))
    except Exception:
        return "Veri Yok"


def _format_try(value) -> str:
    return f"{_to_float(value):,.0f} TL"


def _format_pct(value) -> str:
    return f"%{_to_float(value):.1f}"


def _format_signed_try(value) -> str:
    amount = _to_float(value)
    sign = "+" if amount > 0 else ""
    return f"{sign}{amount:,.0f} TL"


def _fundpilot_comment(row: pd.Series) -> str:
    usd_exposure = _to_float(row.get("currency_exposure_usd"))
    equity_exposure = _to_float(row.get("equity_exposure"))
    money_market_exposure = _to_float(row.get("money_market_exposure"))

    if usd_exposure >= 70:
        return (
            "Bu fon portfoyde belirgin USD/yabanci varlik etkisi tasiyor. "
            "Kur hareketleri performans uzerinde daha gorunur olabilir."
        )

    if equity_exposure >= 80:
        return (
            "Bu fon hisse yogun bir rol ustleniyor. Getiri potansiyeliyle "
            "birlikte kisa vadeli oynaklik etkisi de izlenmeli."
        )

    if money_market_exposure >= 30:
        return (
            "Bu fon daha defansif ve likit bir tampon rolunde. Stres "
            "donemlerinde portfoy dengesine destek olabilir."
        )

    return (
        "Bu fon karma veya tamamlayici bir rol ustleniyor. Tema, kur ve "
        "likidite etkileri portfoyun geneliyle birlikte okunmali."
    )


def _render_metric_strip(row: pd.Series) -> None:
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Guncel Deger", _format_try(row.get("current_value")))
    with metric_cols[1]:
        st.metric("K/Z", _format_signed_try(row.get("pnl")))
    with metric_cols[2]:
        st.metric("Agirlik", _format_pct(row.get("actual_weight")))
    with metric_cols[3]:
        st.metric("Risk", _to_int_label(row.get("risk_value")))


def _render_exposure_grid(row: pd.Series) -> None:
    exposure_cols = st.columns(5)
    with exposure_cols[0]:
        st.metric("USD", _format_pct(row.get("currency_exposure_usd")))
    with exposure_cols[1]:
        st.metric("EUR", _format_pct(row.get("currency_exposure_eur")))
    with exposure_cols[2]:
        st.metric("TL", _format_pct(row.get("currency_exposure_tl")))
    with exposure_cols[3]:
        st.metric("Hisse", _format_pct(row.get("equity_exposure")))
    with exposure_cols[4]:
        st.metric("Para Piyasasi", _format_pct(row.get("money_market_exposure")))


def _render_detail_content(row: pd.Series) -> None:
    fund_code = str(row.get("fund_code", "Fon"))
    fund_name = str(row.get("fund_name", fund_code))
    theme_primary = str(row.get("theme_primary", "Tema Yok"))
    theme_secondary = str(row.get("theme_secondary", "Alt Tema Yok"))
    category = str(row.get("category", "Kategori Yok"))

    st.markdown(
        f"""
        <div class="fp-detail-panel">
            <div class="fp-detail-kicker">Secili Fon</div>
            <div class="fp-detail-title">{fund_code}</div>
            <div class="fp-detail-name">{fund_name}</div>
            <div class="fp-detail-meta">{category} | {theme_primary} / {theme_secondary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_metric_strip(row)
    _render_exposure_grid(row)

    st.markdown("**FonPilot Yorumu**")
    st.info(_fundpilot_comment(row))


def render_fund_detail_dialog(row: pd.Series) -> None:
    fund_code = str(row.get("fund_code", "Fon"))

    st.markdown(
        """
        <style>
        .fp-detail-panel {
            border: 1px solid #d9e1ea;
            border-radius: 10px;
            padding: 13px 14px;
            background: #ffffff;
            margin-bottom: 10px;
        }
        .fp-detail-kicker {
            color: #64748b;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .04em;
        }
        .fp-detail-title {
            color: #111827;
            font-size: 22px;
            font-weight: 850;
            line-height: 1.1;
            margin-top: 4px;
        }
        .fp-detail-name {
            color: #1f2937;
            font-size: 14px;
            font-weight: 700;
            line-height: 1.35;
            margin-top: 4px;
        }
        .fp-detail-meta {
            color: #64748b;
            font-size: 12px;
            line-height: 1.35;
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if hasattr(st, "dialog"):

        @st.dialog(f"{fund_code} Detay", width="large")
        def _dialog() -> None:
            _render_detail_content(row)

        _dialog()
        return

    st.warning("Bu Streamlit surumunde dialog desteklenmiyor; detay inline gosteriliyor.")
    _render_detail_content(row)
