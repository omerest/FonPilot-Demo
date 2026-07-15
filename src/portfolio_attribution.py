import pandas as pd


ATTRIBUTION_COLUMNS = [
    "fund_code",
    "pnl",
    "fund_return_pct",
    "portfolio_pnl_contribution_pct",
    "profit_efficiency",
]


def build_fund_pnl_attribution(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=ATTRIBUTION_COLUMNS)

    result = df.copy()
    result["pnl"] = pd.to_numeric(result.get("pnl", 0), errors="coerce").fillna(0)

    if "return_pct" in result.columns:
        result["fund_return_pct"] = pd.to_numeric(
            result["return_pct"],
            errors="coerce",
        ).fillna(0)
    else:
        cost_basis = pd.to_numeric(
            result.get("total_cost", result.get("cost_value", 0)),
            errors="coerce",
        ).fillna(0)
        result["fund_return_pct"] = 0.0
        valid_cost = cost_basis != 0
        result.loc[valid_cost, "fund_return_pct"] = (
            result.loc[valid_cost, "pnl"] / cost_basis.loc[valid_cost]
        ) * 100

    total_portfolio_pnl = float(result["pnl"].sum())
    if total_portfolio_pnl != 0:
        result["portfolio_pnl_contribution_pct"] = (
            result["pnl"] / total_portfolio_pnl
        ) * 100
    else:
        result["portfolio_pnl_contribution_pct"] = 0.0

    result["profit_efficiency"] = pd.NA

    if abs(total_portfolio_pnl) > 1e-9 and total_portfolio_pnl > 0:
        if "actual_weight" in result.columns:
            portfolio_weight_pct = pd.to_numeric(
                result["actual_weight"],
                errors="coerce",
            )
        else:
            portfolio_weight_pct = pd.Series(0.0, index=result.index)

        valid_efficiency = (
            (result["pnl"] > 0)
            & (result["portfolio_pnl_contribution_pct"] > 0)
            & (portfolio_weight_pct > 0)
        )

        result.loc[valid_efficiency, "profit_efficiency"] = (
            result.loc[valid_efficiency, "portfolio_pnl_contribution_pct"]
            / portfolio_weight_pct.loc[valid_efficiency]
        )

        result["profit_efficiency"] = pd.to_numeric(
            result["profit_efficiency"],
            errors="coerce",
        ).replace([float("inf"), -float("inf")], pd.NA)

    return result[ATTRIBUTION_COLUMNS].sort_values(
        "pnl",
        ascending=False,
    )
