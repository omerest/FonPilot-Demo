def _to_float(value, default=0):
    try:
        return float(value)
    except Exception:
        return default


def _regime_comment(regime_name: str) -> str:
    comments = {
        "Altin / Emtia Dominant": (
            "Portfoy davranisi altin/emtia soklarina daha yakin duruyor. "
            "Bu skor iyi veya kotu degil, baskin davranis faktorunu gosterir."
        ),
        "USD Dominant": (
            "Portfoy davranisi kur hareketlerine belirgin sekilde duyarlidir. "
            "Bu skor getiri tahmini degil, kur hassasiyet profilidir."
        ),
        "Defansif Gelir": (
            "Portfoy daha cok para piyasasi/defansif katmana yakin duruyor. "
            "Skor dusuk risk tavsiyesi degil, varlik dagilimi profilidir."
        ),
        "Agresif Buyume": (
            "Portfoy hisse/buyume faktoruyle daha yuksek beta davranisi gosterebilir."
        ),
        "Buyume": (
            "Portfoy buyume varliklarina duyarlidir ancak agresif esigin altindadir."
        ),
        "Dengeli": (
            "Portfoy ne belirgin sekilde defansif ne de agresif konumda. "
            "Riskli varliklar ile koruyucu/nakit bilesenler yaklasik denge olusturuyor. "
            "Bu skor iyi veya kotu degildir; portfoy davranis profilini gosterir."
        ),
    }
    return comments.get(regime_name, "Portfoy davranis profili siniflandirilamadi.")


def _build_result(
    regime_name: str,
    score: float,
    driver: str,
    macro_sensitivity: str,
    positive_factors: list[str],
    negative_factors: list[str],
) -> dict:
    return {
        "regime_name": regime_name,
        "score": round(score),
        "driver": driver,
        "macro_sensitivity": macro_sensitivity,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "comment": _regime_comment(regime_name),
        "definition": "Asset-allocation regime indicator; not a buy/sell signal.",
    }


def detect_portfolio_regime(
    exposure_summary: dict,
) -> dict:

    usd = _to_float(exposure_summary.get("usd_exposure", 0))
    gold = _to_float(exposure_summary.get("gold_exposure", 0))
    equity = _to_float(exposure_summary.get("equity_exposure", 0))
    money_market = _to_float(exposure_summary.get("money_market_exposure", 0))

    risk_like = equity + usd * 0.5
    defensive_like = money_market + gold * 0.5

    if gold >= 25:
        return _build_result(
            "Altin / Emtia Dominant",
            gold,
            "Altin",
            "Gold",
            [f"Altin exposure %{gold:.1f}"],
            [f"Para piyasasi exposure %{money_market:.1f}"],
        )

    if usd >= 45:
        return _build_result(
            "USD Dominant",
            usd,
            "USD",
            "USD",
            [f"USD exposure %{usd:.1f}"],
            [f"TL/para piyasasi katmani %{money_market:.1f}"],
        )

    if money_market >= 40 and equity < 25:
        return _build_result(
            "Defansif Gelir",
            money_market,
            "Para Piyasasi",
            "TCMB Policy Rate",
            [f"Para piyasasi exposure %{money_market:.1f}"],
            [f"Hisse exposure %{equity:.1f}"],
        )

    if equity >= 60:
        return _build_result(
            "Agresif Buyume",
            equity,
            "Hisse",
            "BIST / Nasdaq",
            [f"Hisse exposure %{equity:.1f}"],
            [f"Defansif katman %{defensive_like:.1f}"],
        )

    if equity >= 40:
        return _build_result(
            "Buyume",
            equity,
            "Hisse",
            "BIST / Nasdaq",
            [f"Hisse exposure %{equity:.1f}"],
            [f"Defansif katman %{defensive_like:.1f}"],
        )

    return _build_result(
        "Dengeli",
        50,
        "Coklu Varlik",
        "Mixed",
        [f"Riskli varlik proxy %{risk_like:.1f}"],
        [f"Koruyucu/nakit proxy %{defensive_like:.1f}"],
    )
