import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import DB_PATH, IS_DEMO_MODE, METADATA_CSV_PATH
from src.risk_engine import calculate_risk_engine, generate_awareness_feed, calculate_exposure_summary, calculate_performance_attribution, calculate_liquidity_exit_summary, calculate_theme_exposure_summary, calculate_portfolio_health, calculate_data_quality, run_macro_scenario, calculate_snapshot_change_tracker, calculate_scenario_drivers
from src.portfolio_read_model import load_portfolio_read_model
from src.regime_engine import detect_portfolio_regime
from src.market_data_engine import get_market_pulse
from ui.components import render_section_header
from ui.pages.dashboard_sections import render_portfolio_change_tracker
from ui.pages.fund_explorer import render_fund_detail_dialog

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
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if IS_DEMO_MODE:
    st.info(
        "FONPILOT demo mode is active. Sample data is used and write actions are disabled."
    )

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
    if IS_DEMO_MODE:
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

    with get_connection() as conn:
        snapshots_df = pd.read_sql_query(
            """
            SELECT *
            FROM portfolio_snapshots
            ORDER BY snapshot_date ASC, created_at ASC
            """,
            conn,
        )

    return snapshots_df

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

    print(
        f"Market Pulse Error: {e}"
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

total_cost = df["total_cost"].sum()
total_value = df["current_value"].sum()
total_pnl = df["pnl"].sum()
total_return = (total_pnl / total_cost) * 100

daily_pnl_total = df["daily_pnl"].sum()

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
if "position_update_message" in st.session_state:

    st.info(
        st.session_state["position_update_message"]
    )

    del st.session_state["position_update_message"]
st.caption(
    "Personal Fund Awareness System · Local MVP · TEFAS + SQLite"
)

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

        st.metric(
            label,
            format_tr_number(data["price"]),
            format_tr_percent(data["change_pct"]),
        )

with pulse_cols[8]:

    st.metric(
        risk_appetite["regime"],
        f"%{risk_appetite['score']}",
        "Risk İştahı",
    )

st.caption(
    f"Kaynak: Yahoo Finance | Son Güncelleme: {market_pulse['updated_at']}"
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

st.markdown(
    "<h3 style='color:#38bdf8;'>📡 Portföy Rejimi</h3>",
    unsafe_allow_html=True,
)

regime_cols = st.columns(4)

with regime_cols[0]:
    st.metric(
        "Rejim",
        portfolio_regime["regime_name"],
    )

with regime_cols[1]:
    st.metric(
        "Skor",
        portfolio_regime["score"],
    )

with regime_cols[2]:
    st.metric(
        "Ana Sürücü",
        portfolio_regime["driver"],
    )

with regime_cols[3]:
    st.metric(
        "Makro Hassasiyet",
        portfolio_regime["macro_sensitivity"],
    )

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



st.markdown("### K11A · Historical Snapshot Trend")

st.info("Demo repository is read-only. Snapshot save is disabled.")
    
if "snapshot_message" in st.session_state:

    st.success(st.session_state["snapshot_message"])

    del st.session_state["snapshot_message"]

if len(snapshots_df) >= 1:

    latest_snapshot_summary = snapshots_df.iloc[-1]

    ss1, ss2 = st.columns(2)

    with ss1:
        st.metric(
            "Son Snapshot",
            latest_snapshot_summary["snapshot_date"],
        )

    with ss2:
        st.metric(
            "Snapshot Sayısı",
            len(snapshots_df),
        )


if len(snapshots_df) >= 1:

    trend_cols = st.columns(4)

    latest_snapshot = snapshots_df.iloc[-1]

    with trend_cols[0]:
        st.metric(
            "Risk Skoru",
            f"{latest_snapshot['risk_score']}/100",
        )

    with trend_cols[1]:
        st.metric(
            "USD Exposure",
            f"%{latest_snapshot['usd_exposure']}",
        )

    with trend_cols[2]:
        st.metric(
            "Hisse Exposure",
            f"%{latest_snapshot['equity_exposure']}",
        )

    with trend_cols[3]:
        st.metric(
            "Likidite",
            f"{latest_snapshot['liquidity_score']}/100",
        )

    trend_df = snapshots_df.copy()

    trend_df["snapshot_date"] = pd.to_datetime(
        trend_df["snapshot_date"]
    )

    range_choice = st.radio(
        "Trend Aralığı",
        ["1 Gün", "3 Ay", "6 Ay", "12 Ay"],
        horizontal=True,
        key="snapshot_trend_range",
    )

    today = pd.Timestamp.today().normalize()

    range_days = {
        "1 Gün": 1,
        "3 Ay": 90,
        "6 Ay": 180,
        "12 Ay": 365,
    }

    start_date = today - pd.Timedelta(
        days=range_days[range_choice]
    )

    filtered_trend_df = trend_df[
        trend_df["snapshot_date"] >= start_date
    ]

    fig = px.line(
        filtered_trend_df,
        x="snapshot_date",
        y=[
            "risk_score",
            "usd_exposure",
            "equity_exposure",
            "volatility_score",
        ],
        markers=True,
    )

    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title=None,
        yaxis_title=None,
        legend_title=None,
    )

    fig.update_xaxes(
        tickformat="%d.%m.%Y",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )
    
else:
    st.info("Henüz yeterli snapshot verisi yok.")

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

    fig = px.bar(
        df,
        x="fund_code",
        y="pnl",
        text="return_pct",
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )

    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=0, b=0),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

st.divider()

st.markdown(
    "<h3 style='color:#ef4444;'>⚠️ K07 · Risk Intelligence Center</h3>",
    unsafe_allow_html=True,
)

risk_main, r1, r2, r3, r4, r5 = st.columns([1.4, 1, 1, 1, 1, 1])

with risk_main:
    st.metric(
        "Genel Risk Skoru",
        f"{overall_risk_score}/100",
        overall_risk_level,
    )

component_list = list(risk_components.values())

for col, item in zip([r1, r2, r3, r4, r5], component_list):
    with col:
        st.metric(
            item["label"],
            f"{item['score']}/100",
            item["level"],
        )

st.markdown("#### Risk Insight Feed")

for item in component_list:
    if item["score"] >= 75:
        icon = "🔴"
    elif item["score"] >= 55:
        icon = "🟠"
    elif item["score"] >= 35:
        icon = "🟡"
    else:
        icon = "🟢"

    with st.expander(
        f"{icon} {item['label']} · {item['score']}/100 · {item['level']}",
        expanded=item["score"] >= 75,
    ):
        st.write(f"**Durum:** {item['main_metric']}")
        st.write(item["reason"])

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
    "<h3 style='color:#a855f7;'>🧠 K10A · Performance Attribution Engine</h3>",
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

st.markdown(
    "<h3 style='color:#f59e0b;'>🔮 K16 · Macro Scenario Simulator</h3>",
    unsafe_allow_html=True,
)

scenario_col1, scenario_col2 = st.columns(2)

with scenario_col1:

    selected_scenario = st.selectbox(
        "Senaryo",
        [
            "USD Forecast",
            "Gold Forecast",
            "Nasdaq Forecast",
            "BIST Forecast",
        ],
        key="macro_scenario_select",
    )

with scenario_col2:

    shock_percent = st.slider(
        "Forecast (%)",
        min_value=-30,
        max_value=30,
        value=10,
        step=1,
        key="macro_scenario_slider",
    )

scenario_result = run_macro_scenario(
    selected_scenario,
    shock_percent,
)

scenario_drivers_df = calculate_scenario_drivers(
    selected_scenario,
    shock_percent,
)

sr1, sr2 = st.columns(2)

with sr1:

    st.metric(
        "Tahmini Etki (%)",
        f"%{scenario_result['estimated_impact_pct']}",
    )

with sr2:

    st.metric(
        "Tahmini Etki (TL)",
        f"{scenario_result['estimated_impact_tl']:,.0f} TL",
    )

st.info(
    scenario_result["comment"]
)

st.markdown("#### K16A · Scenario Driver Breakdown")
show_all_drivers = st.checkbox(
    "Tüm fonları göster",
    value=False,
    key="show_all_scenario_drivers",
)

if len(scenario_drivers_df) == 0:

    st.info(
        "Senaryo driver verisi oluşmadı."
    )

else:

    display_df = scenario_drivers_df.copy()

    if not show_all_drivers:
        display_df = display_df.head(5)


    display_df["estimated_effect_pct"] = (
        display_df["estimated_effect_pct"]
        .round(2)
    )

    display_df["estimated_effect_tl"] = (
        display_df["estimated_effect_tl"]
        .round(0)
    )

    st.dataframe(
        display_df.rename(
            columns={
                "fund_code": "Fon",
                "estimated_effect_pct": "Etki %",
                "estimated_effect_tl": "Etki TL",
                "theme_primary": "Tema",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    
st.divider()


st.markdown("### K08 · AI Portfolio Awareness Feed")

feed_cols = st.columns(5)

for item in awareness_feed:

    if item["severity"] == "Kritik":
        badge = "🔴 Kritik"
    elif item["severity"] == "İzlenmeli":
        badge = "🟠 İzlenmeli"
    elif item["severity"] == "Orta":
        badge = "🟡 Orta"
    else:
        badge = "🟢 Kontrollü"

    col = feed_cols[
        awareness_feed.index(item) % 5
    ]

    with col:


        with st.container(border=True):
        
            st.markdown(
                f"""
                <div style="font-size:12px; line-height:1.25;">
                    <b>{item['icon']} {item['title']}</b><br>
                    <span style="color:#9ca3af;">
                        {badge} · Risk: {item['score']}/100
                    </span><br>
                    <span>{item['message']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

st.markdown("### K08A · Liquidity / Exit Engine")

liq_top, liq_stats = st.columns([1.2, 1])

with liq_top:

    st.metric(
        "Likidite Skoru",
        f"{liquidity_data['liquidity_score']}/100",
        liquidity_data["level"],
    )

    st.caption(
        f"Ağırlıklı Ortalama Satış Valörü: "
        f"T+{liquidity_data['weighted_sell_value']}"
    )

    st.info(liquidity_data["insight"])

with liq_stats:

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Anlık",
            f"%{liquidity_data['instant_ratio']}",
        )

    with c2:
        st.metric(
            "Orta",
            f"%{liquidity_data['medium_ratio']}",
        )

    with c3:
        st.metric(
            "Yavaş",
            f"%{liquidity_data['slow_ratio']}",
        )

    with c4:
        st.metric(
            "PPF",
            f"%{liquidity_data['money_market_ratio']}",
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


render_portfolio_change_tracker(snapshot_changes)

st.divider()

st.markdown(
    '<div class="section-title">K12 · Fon Tablosu</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Demo repository is read-only. Position edit, delete, TEFAS refresh, and metadata writes are not available."
)

detail_options = df["fund_code"].astype(str).tolist()
detail_name_map = (
    df.set_index("fund_code")["fund_name"].astype(str).to_dict()
    if "fund_name" in df.columns
    else {}
)

detail_select_col, detail_action_col = st.columns([2.5, 1])

with detail_select_col:
    selected_detail_fund = st.selectbox(
        "Tablodan detay için fon seç",
        detail_options,
        format_func=lambda code: (
            f"{code} - {detail_name_map.get(code, code)}"
        ),
        key="k12_detail_selectbox",
    )

with detail_action_col:
    st.write("")
    st.write("")
    open_detail_dialog = st.button(
        "Detay Penceresini Aç",
        key="k12_open_detail_dialog",
        use_container_width=True,
    )

if open_detail_dialog:
    selected_dialog_rows = df[
        df["fund_code"].astype(str) == str(selected_detail_fund)
    ]
    if not selected_dialog_rows.empty:
        render_fund_detail_dialog(selected_dialog_rows.iloc[0])

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

display_df = display_df.rename(

    columns={
        "fund_code": "Fon",
        "currency": "Kur",
        "current_value": "Güncel Değer",
        "pnl": "K/Z",
        "return_pct": "Getiri %",
        "actual_weight": "Ağırlık %",
        "daily_return_pct": "Günlük %",
    }
)

for col in [
    "Güncel Değer",
    "K/Z",
    "Getiri %",
    "Ağırlık %",
    "Günlük %",
]:

    display_df[col] = display_df[col].map(
        lambda x: f"{x:,.2f}"
    )

st.dataframe(
    
    display_df.style.set_properties(
        subset=[
            "Güncel Değer",
            "K/Z",
            "Getiri %",
            "Ağırlık %",
            "Günlük %",
        ],
        **{"text-align": "right"},
    ).map(
        color_pnl,
        subset=[
            "K/Z",
            "Getiri %",
            "Günlük %",
        ],
    ),
    use_container_width=True,
    hide_index=True,
)
