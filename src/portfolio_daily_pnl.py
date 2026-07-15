import pandas as pd


def _get_market_price(market_pulse: dict, key: str, default: float = 1.0) -> float:
    try:
        value = float(market_pulse.get(key, {}).get("price", default))
        if value > 0:
            return value
    except Exception:
        pass

    return default


def build_daily_pnl_try_audit(df: pd.DataFrame, market_pulse: dict) -> dict:
    if df is None or df.empty:
        return {
            "total": 0.0,
            "rows": pd.DataFrame(),
            "fx_rates": {"TL": 1.0, "TRY": 1.0, "USD": 1.0, "EUR": 1.0},
        }

    fx_rates = {
        "TL": 1.0,
        "TRY": 1.0,
        "USD": _get_market_price(market_pulse, "USDTRY"),
        "EUR": _get_market_price(market_pulse, "EURTRY"),
    }

    audit_df = df.copy()
    audit_df["currency"] = (
        audit_df.get("currency", "TL")
        .fillna("TL")
        .astype(str)
        .str.upper()
        .str.strip()
    )
    audit_df["daily_pnl_native"] = pd.to_numeric(
        audit_df.get("daily_pnl", 0),
        errors="coerce",
    ).fillna(0)
    audit_df["daily_pnl_fx_rate"] = audit_df["currency"].map(fx_rates).fillna(1.0)
    audit_df["daily_pnl_try"] = (
        audit_df["daily_pnl_native"]
        * audit_df["daily_pnl_fx_rate"]
    )

    return {
        "total": float(audit_df["daily_pnl_try"].sum()),
        "rows": audit_df,
        "fx_rates": fx_rates,
    }
