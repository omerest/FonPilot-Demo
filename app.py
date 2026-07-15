from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import IS_DEMO_MODE, METADATA_CSV_PATH
from src.risk_engine import calculate_risk_engine, generate_awareness_feed, calculate_exposure_summary, calculate_performance_attribution, calculate_liquidity_exit_summary, calculate_theme_exposure_summary, calculate_portfolio_health, calculate_data_quality, run_macro_scenario, calculate_snapshot_change_tracker, calculate_scenario_drivers
from src.portfolio_read_model import load_portfolio_read_model
from src.regime_engine import detect_portfolio_regime
from src.market_data_engine import get_market_pulse
from src.portfolio_daily_pnl import build_daily_pnl_try_audit
from src.macro_data_provider import fetch_tcmb_policy_rate
from ui.pages.navigation_shell import render_main_navigation
from ui.pages.overview_page import render_overview_page
from ui.pages.risk_page import render_risk_page
from ui.pages.exposure_page import render_exposure_page
from ui.pages.macro_page import render_macro_page
from ui.pages.funds_page import render_funds_page
from ui.pages.history_page import render_history_page

METADATA_PATH = METADATA_CSV_PATH

st.set_page_config(
    page_title="FONPILOT",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>

    .main {
        padding-top: 0.25rem;
    }
[data-testid="stAppViewContainer"] {
    border-top: 4px solid #38bdf8;
}
    h1 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    h2 {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
    }

    h3 {
        font-size: 1.02rem !important;
        font-weight: 850 !important;
        margin-top: 0.45rem !important;
        margin-bottom: 0.35rem !important;
        color: #0f172a !important;
        letter-spacing: 0 !important;
    }

    h4 {
        font-size: 0.92rem !important;
        font-weight: 800 !important;
        margin-top: 0.45rem !important;
        margin-bottom: 0.28rem !important;
        color: #334155 !important;
    }

    .stMetric {
        border-radius: 8px;
        padding: 0;
    }

    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e5eaf1;
        padding: 8px 10px;
        border-radius: 8px;
        min-height: 82px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.18rem !important;
    }

    div[data-testid="metric-container"] > label {
        margin-bottom: 0px !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.02rem !important;
        line-height: 1.12 !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
        font-size: 0.68rem !important;
        font-weight: 750 !important;
        color: #64748b !important;
    }
    div.stButton > button {
    background-color: #4b5563;
    color: white;
    border: 1px solid #6b7280;
    }

    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.75rem;
        padding-bottom: 1.2rem;
        padding-left: 2.1rem;
        padding-right: 2.1rem;
        max-width: 1600px;
    }

    h1 {
        font-size: 30px !important;
        margin-bottom: 0.08rem !important;
    }

    .fp-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 10px 11px;
        min-height: 94px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        border: 1px solid #e5eaf1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .fp-label {
        font-size: 10px;
        color: #64748b;
        margin-bottom: 5px;
        font-weight: 800;
        letter-spacing: 0;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .fp-value {
        font-size: 20px;
        line-height: 1.15;
        font-weight: 850;
        color: #0f172a;
        letter-spacing: 0;
        word-break: keep-all;
    }

    .fp-sub {
        margin-top: 5px;
        font-size: 10.5px;
        line-height: 1.25;
        color: #64748b;
    }

    .k00-pulse-card {
        background: #ffffff;
        border: 1px solid #e5eaf1;
        border-radius: 8px;
        padding: 8px 9px;
        min-height: 76px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        overflow: hidden;
    }

    .k00-pulse-label {
        color: #64748b;
        font-size: 10px;
        line-height: 1.1;
        font-weight: 800;
        white-space: nowrap;
    }

    .k00-pulse-value {
        color: #0f172a;
        font-size: clamp(13px, 1.05vw, 15px);
        line-height: 1.2;
        font-weight: 850;
        margin-top: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .k00-pulse-delta {
        font-size: 10.5px;
        line-height: 1.15;
        font-weight: 750;
        margin-top: 5px;
        white-space: nowrap;
    }

    .green {
        color: #16a34a !important;
        font-weight: 800;
    }

    .red {
        color: #dc2626 !important;
        font-weight: 800;
    }

    .section-title {
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
        margin: 0.45rem 0 0.35rem 0;
        letter-spacing: 0;
        text-transform: uppercase;
        border-left: 3px solid #38bdf8;
        padding-left: 8px;
    }

    div[data-testid="stMetric"] {
        background: white;
        padding: 8px;
        border-radius: 8px;
        border: 1px solid #e5eaf1;
    }

    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e5eaf1;
    }

    hr {
        margin: 0.45rem 0 !important;
        opacity: 0.35;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 0.45rem !important;
    }

    div[data-testid="stExpander"] {
        border-radius: 8px !important;
        margin-bottom: 0.35rem !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }

        .fp-card {
            min-height: 84px;
        }

        .fp-value {
            font-size: 18px;
        }

        .k00-pulse-card {
            min-height: 70px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if IS_DEMO_MODE:
    st.info(
        "FONPILOT public demo is active. Sample data is used and all write actions are disabled."
    )

def format_try(value):
    return f"{value:,.0f} TL"


def format_tr_number(value):

    try:

        formatted = f"{float(value):,.2f}"

        return (
            formatted
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except Exception:

        return "Veri Yok"

def format_tr_percent(value):

    try:

        formatted = f"{float(value):+.2f}"

        return (
            formatted
            .replace(".", ",")
            + "%"
        )

    except Exception:

        return "Veri Yok"

def color_pnl(val):

    try:

        numeric = float(
            str(val).replace(",", "")
        )

        if numeric > 0:
            return "color: #22c55e"

        if numeric < 0:
            return "color: #ef4444"

        return ""

    except Exception:

        return ""


def calculate_risk_appetite(market_pulse):

    score = 50

    try:

        score += market_pulse["SP500"]["change_pct"] * 8
        score += market_pulse["QQQM"]["change_pct"] * 10
        score += market_pulse["SOXQ"]["change_pct"] * 12
        score += market_pulse["BTC"]["change_pct"] * 4

        score -= market_pulse["DXY"]["change_pct"] * 8

    except Exception:

        pass

    score = max(0, min(100, score))

    if score >= 60:
        regime = "🟢 Risk-ON"
    elif score <= 40:
        regime = "🔴 Risk-OFF"
    else:
        regime = "🟡 Nötr"

    return {
        "score": round(score),
        "regime": regime,
    }


def explain_risk_appetite(market_pulse, risk_appetite):
    indicators = [
        ("SP500", "SP500", 8, "Pozitif"),
        ("QQQM", "QQQM", 10, "Pozitif"),
        ("SOXQ", "SOXQ", 12, "Pozitif"),
        ("BTC", "BTC", 4, "Pozitif"),
        ("DXY", "DXY", -8, "Negatif"),
    ]

    rows = []
    raw_score = 50

    for label, key, multiplier, direction in indicators:
        try:
            change_pct = float(market_pulse.get(key, {}).get("change_pct", 0))
        except Exception:
            change_pct = 0

        contribution = change_pct * multiplier
        raw_score += contribution
        rows.append(
            {
                "Gosterge": label,
                "Degisim %": round(change_pct, 2),
                "Katsayi": multiplier,
                "Katki": round(contribution, 2),
                "Yon": direction,
            }
        )

    score = risk_appetite.get("score", 0)

    if score >= 60:
        reason = "Skor 60 ve uzerinde oldugu icin sonuc Risk-On."
    elif score <= 40:
        reason = "Skor 40 ve altinda oldugu icin sonuc Risk-Off."
    else:
        reason = "Skor 40-60 bandinda oldugu icin sonuc Neutral."

    return {
        "base_score": 50,
        "raw_score": round(raw_score, 2),
        "score": score,
        "regime": risk_appetite.get("regime", "Veri Yok"),
        "rows": rows,
        "reason": reason,
    }



def load_portfolio():
    df = load_portfolio_read_model()

    print(
        df[
            [
                "fund_code",
                "daily_return_pct",
                "daily_pnl",
            ]
        ].head()
    )


    return df

def load_snapshots():
    return pd.DataFrame(
        [
            {
                "snapshot_date": "2026-01-13",
                "total_value": 56000,
                "total_pnl": 1800,
                "risk_score": 47,
                "usd_exposure": 31.2,
                "equity_exposure": 39.8,
                "liquidity_score": 42,
                "volatility_score": 39,
                "created_at": "2026-01-13T00:00:00",
            },
            {
                "snapshot_date": "2026-01-14",
                "total_value": 57150,
                "total_pnl": 2250,
                "risk_score": 46,
                "usd_exposure": 30.4,
                "equity_exposure": 40.2,
                "liquidity_score": 41,
                "volatility_score": 38,
                "created_at": "2026-01-14T00:00:00",
            },
            {
                "snapshot_date": "2026-01-15",
                "total_value": 58620,
                "total_pnl": 3120,
                "risk_score": 44,
                "usd_exposure": 29.7,
                "equity_exposure": 41.5,
                "liquidity_score": 40,
                "volatility_score": 37,
                "created_at": "2026-01-15T00:00:00",
            },
        ]
    )

df = load_portfolio()
snapshots_df = load_snapshots()

global_metadata_df = pd.read_csv(METADATA_PATH)

global_metadata_df["fund_code"] = (
    global_metadata_df["fund_code"]
    .astype(str)
    .str.upper()
    .str.strip()
)

risk_data = calculate_risk_engine()

overall_risk_score = risk_data["overall_score"]
overall_risk_level = risk_data["overall_level"]

risk_components = risk_data["components"]

awareness_feed = generate_awareness_feed(risk_data)
exposure_summary = calculate_exposure_summary()
try:

    market_pulse = get_market_pulse()

    risk_appetite = calculate_risk_appetite(
        market_pulse
    )

except Exception as e:

    market_pulse = {}
    risk_appetite = {
        "score": 50,
        "regime": "Neutral",
    }

    print(
        f"Market Pulse Error: {e}"
    )

risk_appetite_detail = explain_risk_appetite(
    market_pulse,
    risk_appetite,
)

portfolio_regime = detect_portfolio_regime(
    {
        "usd_exposure": exposure_summary["USD"]["value"],
        "gold_exposure": exposure_summary["Altın"]["value"],
        "equity_exposure": exposure_summary["Hisse"]["value"],
        "money_market_exposure": exposure_summary["Para Piyasası"]["value"],
    }
)

attribution_data = calculate_performance_attribution()
liquidity_data = calculate_liquidity_exit_summary()
theme_data = calculate_theme_exposure_summary()
health_data = calculate_portfolio_health()
data_quality = calculate_data_quality()
snapshot_changes = calculate_snapshot_change_tracker()
tcmb_policy_rate = fetch_tcmb_policy_rate()

total_cost = df["total_cost"].sum()
total_value = df["current_value"].sum()
total_pnl = df["pnl"].sum()
total_return = (total_pnl / total_cost) * 100

daily_pnl_audit = build_daily_pnl_try_audit(
    df,
    market_pulse,
)
daily_pnl_total = daily_pnl_audit["total"]

portfolio_value = df["current_value"].sum()

if portfolio_value > 0:

    daily_return_total = (
        daily_pnl_total
        / portfolio_value
    ) * 100

else:

    daily_return_total = 0


latest_date = df["price_date"].max()

positive_count = (df["pnl"] > 0).sum()
negative_count = (df["pnl"] < 0).sum()

usd_funds = (df["currency"] == "USD").sum()
tl_funds = (df["currency"] == "TL").sum()

st.title("FONPILOT")
st.caption(
    "AI Supported TEFAS Investment Intelligence Platform - Public Demo"
)

selected_page = render_main_navigation(is_demo_mode=IS_DEMO_MODE)

page_context = {
    "IS_DEMO_MODE": IS_DEMO_MODE,
    "METADATA_PATH": METADATA_PATH,
    "df": df,
    "market_pulse": market_pulse,
    "risk_appetite": risk_appetite,
    "risk_appetite_detail": risk_appetite_detail,
    "total_pnl": total_pnl,
    "daily_pnl_total": daily_pnl_total,
    "daily_pnl_audit": daily_pnl_audit,
    "total_value": total_value,
    "total_return": total_return,
    "daily_return_total": daily_return_total,
    "tl_funds": tl_funds,
    "usd_funds": usd_funds,
    "positive_count": positive_count,
    "negative_count": negative_count,
    "portfolio_regime": portfolio_regime,
    "exposure_summary": exposure_summary,
    "snapshots_df": snapshots_df,
    "snapshot_changes": snapshot_changes,
    "tcmb_policy_rate": tcmb_policy_rate,
    "overall_risk_score": overall_risk_score,
    "overall_risk_level": overall_risk_level,
    "risk_components": risk_components,
    "theme_data": theme_data,
    "attribution_data": attribution_data,
    "awareness_feed": awareness_feed,
    "liquidity_data": liquidity_data,
    "health_data": health_data,
    "data_quality": data_quality,
    "format_try": format_try,
    "format_tr_number": format_tr_number,
    "format_tr_percent": format_tr_percent,
    "color_pnl": color_pnl,
    "run_macro_scenario": run_macro_scenario,
    "calculate_scenario_drivers": calculate_scenario_drivers,
}

if selected_page == "Overview":
    render_overview_page(page_context)
elif selected_page == "Risk":
    render_risk_page(page_context)
elif selected_page == "Exposure":
    render_exposure_page(page_context)
elif selected_page == "Macro":
    render_macro_page(page_context)
elif selected_page == "Funds":
    render_funds_page(page_context)
elif selected_page == "History":
    render_history_page(page_context)
