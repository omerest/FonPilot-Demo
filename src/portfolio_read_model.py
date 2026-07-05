import sqlite3

import pandas as pd

from src.config import DB_PATH, IS_DEMO_MODE, METADATA_CSV_PATH, PORTFOLIO_CSV_PATH


METADATA_PATH = METADATA_CSV_PATH

READ_MODEL_COLUMNS = [
    "fund_code",
    "entry_type",
    "units",
    "avg_cost",
    "currency",
    "target_weight",
    "latest_price",
    "previous_price",
    "latest_price_date",
    "previous_price_date",
    "latest_price_id",
    "latest_price_source",
    "latest_price_created_at",
    "current_value",
    "cost_value",
    "pnl",
    "pnl_pct",
    "daily_pnl",
    "daily_return_pct",
    "actual_weight",
    # Backward-compatible aliases used by app.py.
    "price",
    "price_date",
    "total_cost",
    "return_pct",
]


def _empty_read_model() -> pd.DataFrame:
    return pd.DataFrame(columns=READ_MODEL_COLUMNS)


def _load_demo_read_model() -> pd.DataFrame:
    portfolio_df = pd.read_csv(PORTFOLIO_CSV_PATH)
    metadata_df = pd.read_csv(METADATA_CSV_PATH)

    portfolio_df["fund_code"] = (
        portfolio_df["fund_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )
    metadata_df["fund_code"] = (
        metadata_df["fund_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df = portfolio_df.merge(
        metadata_df,
        on="fund_code",
        how="left",
    )

    price_factors = [1.08, 0.97, 1.12, 1.04, 1.01]
    previous_factors = [1.06, 0.98, 1.10, 1.03, 1.00]

    df["latest_price"] = [
        round(float(avg_cost) * price_factors[idx % len(price_factors)], 6)
        for idx, avg_cost in enumerate(df["avg_cost"])
    ]
    df["previous_price"] = [
        round(float(avg_cost) * previous_factors[idx % len(previous_factors)], 6)
        for idx, avg_cost in enumerate(df["avg_cost"])
    ]
    df["latest_price_date"] = "2026-01-15"
    df["previous_price_date"] = "2026-01-14"
    df["latest_price_id"] = range(1, len(df) + 1)
    df["latest_price_source"] = "sample_data"
    df["latest_price_created_at"] = "2026-01-15T00:00:00"

    return _finalize_read_model(df)


def _finalize_read_model(df: pd.DataFrame) -> pd.DataFrame:
    df["cost_value"] = df["units"] * df["avg_cost"]
    df["current_value"] = df["units"] * df["latest_price"]

    df["daily_return_pct"] = (
        (
            df["latest_price"]
            - df["previous_price"]
        )
        / df["previous_price"]
    ) * 100

    df["daily_return_pct"] = (
        df["daily_return_pct"]
        .fillna(0)
    )

    df["daily_pnl"] = (
        df["units"]
        * (
            df["latest_price"]
            - df["previous_price"]
        )
    )

    df["daily_pnl"] = (
        df["daily_pnl"]
        .fillna(0)
    )

    df["pnl"] = df["current_value"] - df["cost_value"]
    df["pnl_pct"] = (
        df["pnl"] / df["cost_value"]
    ) * 100

    total_value = df["current_value"].sum()

    if total_value > 0:
        df["actual_weight"] = (
            df["current_value"] / total_value
        ) * 100
    else:
        df["actual_weight"] = 0

    df["price"] = df["latest_price"]
    df["price_date"] = df["latest_price_date"]
    df["total_cost"] = df["cost_value"]
    df["return_pct"] = df["pnl_pct"]

    return df


def load_portfolio_read_model() -> pd.DataFrame:
    try:
        if IS_DEMO_MODE:
            return _load_demo_read_model()

        with sqlite3.connect(DB_PATH) as conn:
            portfolio_df = pd.read_sql_query(
                """
                SELECT *
                FROM portfolio_funds
                """,
                conn,
            )

            latest_prices_df = pd.read_sql_query(
                """
                SELECT
                    fp.fund_code,
                    fp.id AS latest_price_id,
                    fp.price AS latest_price,
                    fp.price_date AS latest_price_date,
                    fp.source AS latest_price_source,
                    fp.created_at AS latest_price_created_at
                FROM fund_prices fp
                INNER JOIN (
                    SELECT fund_code, MAX(price_date) AS latest_date
                    FROM fund_prices
                    GROUP BY fund_code
                ) latest
                ON fp.fund_code = latest.fund_code
                AND fp.price_date = latest.latest_date
                """,
                conn,
            )

            previous_prices_df = pd.read_sql_query(
                """
                WITH ranked AS (
                    SELECT
                        fund_code,
                        price,
                        price_date,
                        ROW_NUMBER() OVER (
                            PARTITION BY fund_code
                            ORDER BY price_date DESC
                        ) AS rn
                    FROM fund_prices
                )
                SELECT
                    fund_code,
                    price AS previous_price,
                    price_date AS previous_price_date
                FROM ranked
                WHERE rn = 2
                """,
                conn,
            )

        for frame in [portfolio_df, latest_prices_df, previous_prices_df]:
            if "fund_code" in frame.columns:
                frame["fund_code"] = (
                    frame["fund_code"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                )

        df = portfolio_df.merge(
            latest_prices_df,
            on="fund_code",
            how="left",
        )

        df = df.merge(
            previous_prices_df,
            on="fund_code",
            how="left",
        )

        if METADATA_PATH.exists():
            metadata_df = pd.read_csv(METADATA_PATH)

            if "fund_code" in metadata_df.columns:
                metadata_df["fund_code"] = (
                    metadata_df["fund_code"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                )

                df = df.merge(
                    metadata_df,
                    on="fund_code",
                    how="left",
                )

        return _finalize_read_model(df)

    except Exception as exc:
        print(f"Portfolio read model error: {exc}")
        return _empty_read_model()
