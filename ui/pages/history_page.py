import pandas as pd
import plotly.express as px
import streamlit as st

from ui.pages.dashboard_sections import render_portfolio_change_tracker


TREND_METRICS = {
    "Portfoy Degeri": {
        "column": "total_value",
        "format": "money",
    },
    "Toplam K/Z": {
        "column": "total_pnl",
        "format": "money",
    },
    "Risk Skoru": {
        "column": "risk_score",
        "format": "score",
    },
    "USD Exposure": {
        "column": "usd_exposure",
        "format": "pct",
    },
    "Equity Exposure": {
        "column": "equity_exposure",
        "format": "pct",
    },
}


def _format_value(value, value_format: str) -> str:
    try:
        numeric_value = float(value)
    except Exception:
        return "-"

    if pd.isna(numeric_value):
        return "-"

    if value_format == "money":
        return f"{numeric_value:,.0f} TL"

    if value_format == "pct":
        return f"%{numeric_value:.1f}"

    if value_format == "score":
        return f"{numeric_value:.1f}/100"

    return f"{numeric_value:,.1f}"


def _safe_change_pct(first_value, last_value) -> float | None:
    try:
        first_float = float(first_value)
        last_float = float(last_value)
    except Exception:
        return None

    if pd.isna(first_float) or pd.isna(last_float) or first_float == 0:
        return None

    return ((last_float - first_float) / abs(first_float)) * 100


def _prepare_snapshot_trend(snapshots_df: pd.DataFrame) -> pd.DataFrame:
    trend_df = snapshots_df.copy()
    trend_df["snapshot_date"] = pd.to_datetime(
        trend_df["snapshot_date"],
        errors="coerce",
    )
    trend_df = trend_df.dropna(subset=["snapshot_date"])

    sort_columns = ["snapshot_date"]

    if "created_at" in trend_df.columns:
        sort_columns.append("created_at")

    return trend_df.sort_values(sort_columns, na_position="last")


def _render_snapshot_summary(snapshots_df: pd.DataFrame) -> None:
    if snapshots_df.empty:
        return

    latest_snapshot = snapshots_df.iloc[-1]
    summary_cols = st.columns(2)

    with summary_cols[0]:
        st.metric("Son Snapshot", latest_snapshot["snapshot_date"])

    with summary_cols[1]:
        st.metric("Snapshot Sayisi", len(snapshots_df))


def _render_trend_chart(snapshots_df: pd.DataFrame) -> None:
    if snapshots_df.empty:
        st.info("Henuz snapshot verisi yok.")
        return

    trend_df = _prepare_snapshot_trend(snapshots_df)

    if trend_df.empty:
        st.info("Snapshot tarihleri okunamadi.")
        return

    metric_label = st.selectbox(
        "Trend metrigi",
        list(TREND_METRICS.keys()),
        key="snapshot_trend_metric",
    )
    metric_config = TREND_METRICS[metric_label]
    metric_column = metric_config["column"]

    available_ranges = {
        "Tum Donem": None,
        "3 Ay": 90,
        "6 Ay": 180,
        "12 Ay": 365,
    }

    range_choice = st.radio(
        "Trend Araligi",
        list(available_ranges.keys()),
        horizontal=True,
        key="snapshot_trend_range",
    )

    filtered_trend_df = trend_df
    range_days = available_ranges[range_choice]

    if range_days is not None:
        latest_date = trend_df["snapshot_date"].max()
        start_date = latest_date - pd.Timedelta(days=range_days)
        filtered_trend_df = trend_df[trend_df["snapshot_date"] >= start_date]

    if metric_column not in filtered_trend_df.columns:
        st.info(f"{metric_label} icin snapshot kolonu bulunamadi.")
        return

    filtered_trend_df = filtered_trend_df.dropna(subset=[metric_column])

    if filtered_trend_df.empty:
        st.info(f"{metric_label} icin yeterli veri yok.")
        return

    first_value = filtered_trend_df.iloc[0][metric_column]
    last_value = filtered_trend_df.iloc[-1][metric_column]
    change_pct = _safe_change_pct(first_value, last_value)

    summary_cols = st.columns(3)

    with summary_cols[0]:
        st.metric(
            "Ilk Deger",
            _format_value(first_value, metric_config["format"]),
        )

    with summary_cols[1]:
        st.metric(
            "Son Deger",
            _format_value(last_value, metric_config["format"]),
        )

    with summary_cols[2]:
        st.metric(
            "Donem Degisimi",
            "-" if change_pct is None else f"%{change_pct:.1f}",
        )

    if len(filtered_trend_df) < 2:
        st.info("Trend grafigi icin en az 2 snapshot gerekli.")
        return

    chart_df = filtered_trend_df.copy()
    chart_df["Donemsel Degisim %"] = (
        chart_df[metric_column].pct_change().replace([float("inf"), -float("inf")], pd.NA)
        * 100
    )

    fig = px.line(
        chart_df,
        x="snapshot_date",
        y=metric_column,
        custom_data=["Donemsel Degisim %"],
    )

    fig.update_traces(
        hovertemplate=(
            "Tarih=%{x|%d.%m.%Y}<br>"
            f"{metric_label}=%{{y:,.2f}}<br>"
            "Donemsel Degisim=%{customdata[0]:.2f}%<extra></extra>"
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title=None,
        yaxis_title=metric_label,
        showlegend=False,
    )
    fig.update_xaxes(tickformat="%d.%m.%Y")

    st.plotly_chart(fig, use_container_width=True)


def render_history_page(context: dict) -> None:
    snapshots_df = context.get("snapshots_df")
    snapshot_changes = context.get("snapshot_changes")

    if snapshots_df is None:
        snapshots_df = pd.DataFrame()

    st.markdown("### K11A ? Historical Snapshot Trend")
    st.caption("Public demo read-only: snapshot save is not available.")

    _render_snapshot_summary(snapshots_df)
    _render_trend_chart(snapshots_df)

    st.divider()

    render_portfolio_change_tracker(snapshot_changes)
