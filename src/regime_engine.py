def detect_portfolio_regime(
    exposure_summary: dict,
) -> dict:

    usd = exposure_summary.get(
        "usd_exposure",
        0,
    )

    gold = exposure_summary.get(
        "gold_exposure",
        0,
    )

    equity = exposure_summary.get(
        "equity_exposure",
        0,
    )

    money_market = exposure_summary.get(
        "money_market_exposure",
        0,
    )

    if gold >= 25:

        return {
            "regime_name": "Altın / Emtia Dominant",
            "score": round(gold),
            "driver": "Altın",
            "macro_sensitivity": "Gold",
        }

    if usd >= 45:

        return {
            "regime_name": "USD Dominant",
            "score": round(usd),
            "driver": "USD",
            "macro_sensitivity": "USD",
        }

    if money_market >= 40 and equity < 25:

        return {
            "regime_name": "Defansif Gelir",
            "score": round(money_market),
            "driver": "Para Piyasası",
            "macro_sensitivity": "USD",
        }

    if equity >= 60:

        return {
            "regime_name": "Agresif Büyüme",
            "score": round(equity),
            "driver": "Hisse",
            "macro_sensitivity": "Nasdaq",
        }

    if equity >= 40:

        return {
            "regime_name": "Büyüme",
            "score": round(equity),
            "driver": "Hisse",
            "macro_sensitivity": "Nasdaq",
        }

    return {
        "regime_name": "Dengeli",
        "score": 50,
        "driver": "Çoklu Varlık",
        "macro_sensitivity": "USD",
    }