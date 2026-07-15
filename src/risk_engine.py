from pathlib import Path

import pandas as pd

import sqlite3
from src.config import DB_PATH, IS_DEMO_MODE
from src.portfolio_read_model import load_portfolio_read_model

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

PORTFOLIO_CSV_PATH = DATA_DIR / "portfolio_funds.csv"
METADATA_CSV_PATH = DATA_DIR / "fund_metadata.csv"


WEIGHTS = {
    "currency": 0.30,
    "concentration": 0.24,
    "liquidity": 0.14,
    "theme": 0.14,
    "volatility": 0.18,
}


SCENARIO_CONFIG = {
    "USD Forecast": {
        "label": "USD/TRY degisim %",
        "unit": "%",
        "exposure_column": "currency_exposure_usd",
        "sensitivity": 1.0,
        "comment": "USD exposure yuksek fonlar kur sokuna daha duyarlidir.",
    },
    "Gold Forecast": {
        "label": "Altin degisim %",
        "unit": "%",
        "exposure_column": "gold_exposure",
        "sensitivity": 1.0,
        "comment": "Altin maruziyeti yuksek fonlar altin sokuna daha duyarlidir.",
    },
    "Nasdaq Forecast": {
        "label": "Nasdaq / global teknoloji degisim %",
        "unit": "%",
        "exposure_columns": ["technology_exposure", "foreign_equity_exposure"],
        "exposure_divisor": 200,
        "sensitivity": 1.0,
        "comment": "Teknoloji ve yabanci hisse yogun fonlar global hisse sokuna daha duyarlidir.",
    },
    "BIST Forecast": {
        "label": "BIST / TL hisse degisim %",
        "unit": "%",
        "exposure_column": "equity_exposure",
        "sensitivity": 1.0,
        "comment": "Hisse yogun fonlar BIST/TL hisse sokuna daha duyarlidir.",
    },
    "TCMB Policy Rate Forecast": {
        "label": "TCMB politika faizi degisimi",
        "unit": "puan",
        "exposure_column": "money_market_exposure",
        "sensitivity": 0.10,
        "comment": (
            "Faiz sokunun getirisi degil, para piyasasi katmaninin politika faizi "
            "duyarliligina iliskin FonPilot heuristic gostergesidir."
        ),
    },
}


def clamp(value: float, min_value: int = 0, max_value: int = 100) -> int:
    try:
        numeric_value = float(value)
    except Exception:
        numeric_value = min_value

    if pd.isna(numeric_value):
        numeric_value = min_value

    return int(max(min_value, min(max_value, round(numeric_value))))


def level_from_score(score: int) -> str:
    if score >= 75:
        return "Kritik"
    if score >= 55:
        return "Yüksek"
    if score >= 35:
        return "Orta"
    return "Düşük"


def load_inputs() -> pd.DataFrame:
    df = load_portfolio_read_model()

    df["position_cost"] = df["units"] * df["avg_cost"]
    total_cost = df["position_cost"].sum()

    if total_cost > 0:
        df["portfolio_weight"] = df["position_cost"] / total_cost * 100
    else:
        df["portfolio_weight"] = 0

    return df

def load_inputs_with_latest_prices() -> pd.DataFrame:
    df = load_inputs()

    df["daily_return_pct"] = (
        (
            df["price"]
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
            df["price"]
            - df["previous_price"]
        )
    )

    df["daily_pnl"] = (
        df["daily_pnl"]
        .fillna(0)
    )


    total_current_value = df["current_value"].sum()

    if total_current_value <= 0:
        total_current_value = 1

    df["current_weight"] = (
        df["current_value"] / total_current_value
    )

    return df

def weighted_average(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns or "portfolio_weight" not in df.columns:
        return 0

    values = pd.to_numeric(df[column], errors="coerce").fillna(0)
    weights = pd.to_numeric(df["portfolio_weight"], errors="coerce").fillna(0)

    return (values * weights).sum() / 100


def weighted_current_value_average(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns or "current_value" not in df.columns:
        return 0

    values = pd.to_numeric(df[column], errors="coerce").fillna(0)
    current_values = pd.to_numeric(df["current_value"], errors="coerce").fillna(0)
    total_current_value = current_values.sum()

    if total_current_value <= 0:
        return 0

    weights = current_values / total_current_value

    return (values * weights).sum()


def calculate_factor_exposure(df: pd.DataFrame, scenario_name: str) -> pd.Series:
    config = SCENARIO_CONFIG.get(scenario_name, {})

    if "exposure_columns" in config:
        exposure = sum(
            pd.to_numeric(
                df[column] if column in df.columns else pd.Series(0, index=df.index),
                errors="coerce",
            ).fillna(0)
            for column in config["exposure_columns"]
        )
        return exposure / config.get("exposure_divisor", 100)

    column = config.get("exposure_column")
    if not column:
        return pd.Series(0, index=df.index)

    values = df[column] if column in df.columns else pd.Series(0, index=df.index)
    return pd.to_numeric(values, errors="coerce").fillna(0) / 100


def calculate_portfolio_factor_exposure(df: pd.DataFrame, scenario_name: str) -> float:
    total_value = pd.to_numeric(df.get("current_value", 0), errors="coerce").fillna(0).sum()

    if total_value <= 0:
        return 0

    weights = pd.to_numeric(df["current_value"], errors="coerce").fillna(0) / total_value
    exposure = calculate_factor_exposure(df, scenario_name)

    return float((weights * exposure).sum() * 100)


def score_currency_risk(df: pd.DataFrame) -> dict:
    usd = weighted_average(df, "currency_exposure_usd")
    eur = weighted_average(df, "currency_exposure_eur")
    gold = weighted_average(df, "gold_exposure")
    foreign_debt = weighted_average(df, "foreign_debt_exposure")

    effective_fx = usd + eur * 0.7 + gold * 0.8 + foreign_debt * 0.8

    score = clamp(effective_fx)

    return {
        "label": "Kur Riski",
        "score": score,
        "level": level_from_score(score),
        "main_metric": f"%{effective_fx:.1f} efektif FX maruziyeti",
        "reason": (
            "USD/EUR, altın ve dış borçlanma maruziyetleri birlikte "
            "portföyün kur hassasiyetini yükseltiyor."
        ),
    }


def score_concentration_risk(df: pd.DataFrame) -> dict:
    top4_funds = df.sort_values("portfolio_weight", ascending=False).head(4)
    top4_weight = top4_funds["portfolio_weight"].sum()

    # MVP proxy:
    # Real top-6 underlying stock concentration will later come from holdings data.
    proxy_top6_stock = (
        weighted_average(df, "technology_exposure") * 0.35
        + weighted_average(df, "equity_exposure") * 0.25
    )

    score = clamp(top4_weight * 0.7 + proxy_top6_stock * 0.8)

    return {
        "label": "Konsantrasyon",
        "score": score,
        "level": level_from_score(score),
        "main_metric": f"İlk 4 fon ağırlığı %{top4_weight:.1f}",
        "reason": (
            "Portföyün önemli kısmı sınırlı sayıda fon ve hisse/tema yoğunluğu "
            "üzerinden taşınıyor olabilir."
        ),
    }


def score_liquidity_risk(df: pd.DataFrame) -> dict:
    weighted_sell_value = weighted_average(df, "sell_value")
    money_market = weighted_average(df, "money_market_exposure")

    # Higher sell value means higher exit risk.
    # Higher money market means lower exit risk.
    score = clamp(weighted_sell_value * 28 - money_market * 0.35 + 25)

    return {
        "label": "Likidite",
        "score": score,
        "level": level_from_score(score),
        "main_metric": f"Ağırlıklı satış valörü T+{weighted_sell_value:.1f}",
        "reason": (
            "Satış valörü, para piyasası oranı ve hızlı nakde dönüş kabiliyeti "
            "portföyün stres anındaki çıkış kalitesini belirler."
        ),
    }


def score_theme_risk(df: pd.DataFrame) -> dict:
    theme_columns = [
        "technology_exposure",
        "banking_exposure",
        "defense_exposure",
        "foreign_equity_exposure",
        "gold_exposure",
        "commodity_exposure",
        "money_market_exposure",
        "blockchain_metaverse_exposure",
    ]

    theme_values = {
        col: weighted_average(df, col)
        for col in theme_columns
    }

    top_theme_value = max(theme_values.values())
    top_theme_name = max(theme_values, key=theme_values.get)

    score = clamp(top_theme_value * 1.15)

    return {
        "label": "Tema Riski",
        "score": score,
        "level": level_from_score(score),
        "main_metric": f"En yoğun tema: {top_theme_name} %{top_theme_value:.1f}",
        "reason": (
            "Aynı tema farklı fonlarda tekrar ediyorsa görünürde çeşitlilik olsa bile "
            "gerçek risk tek hikâyeye sıkışabilir."
        ),
    }


def score_volatility_risk(df: pd.DataFrame) -> dict:
    high_risk_fund_weight = df[df["risk_value"] >= 5]["portfolio_weight"].sum()
    equity = weighted_average(df, "equity_exposure")
    foreign_equity = weighted_average(df, "foreign_equity_exposure")

    score = clamp(
        high_risk_fund_weight * 0.45
        + equity * 0.35
        + foreign_equity * 0.25
    )

    return {
        "label": "Volatilite",
        "score": score,
        "level": level_from_score(score),
        "main_metric": f"Risk 5-7 fon oranı %{high_risk_fund_weight:.1f}",
        "reason": (
            "Yüksek risk değerli fonlar, hisse yoğunluğu ve yabancı hisse etkisi "
            "portföy oynaklığını artırabilir."
        ),
    }


def calculate_risk_engine() -> dict:
    df = load_inputs()

    currency = score_currency_risk(df)
    concentration = score_concentration_risk(df)
    liquidity = score_liquidity_risk(df)
    theme = score_theme_risk(df)
    volatility = score_volatility_risk(df)

    components = {
        "currency": currency,
        "concentration": concentration,
        "liquidity": liquidity,
        "theme": theme,
        "volatility": volatility,
    }

    overall_score = clamp(
        currency["score"] * WEIGHTS["currency"]
        + concentration["score"] * WEIGHTS["concentration"]
        + liquidity["score"] * WEIGHTS["liquidity"]
        + theme["score"] * WEIGHTS["theme"]
        + volatility["score"] * WEIGHTS["volatility"]
    )

    return {
        "overall_score": overall_score,
        "overall_level": level_from_score(overall_score),
        "components": components,
    }

# AI_HOOK:
# Future LLM reasoning layer:
# Generate contextual portfolio awareness insights,
# behavioral finance observations,
# macro-sensitive warnings,
# and narrative investment coaching.
def generate_awareness_feed(result: dict) -> list[dict]:
    feed = []

    for key, item in result["components"].items():
        score = item["score"]
        label = item["label"]

        if score >= 75:
            severity = "Kritik"
            icon = "🔴"
        elif score >= 55:
            severity = "İzlenmeli"
            icon = "🟠"
        elif score >= 35:
            severity = "Orta"
            icon = "🟡"
        else:
            severity = "Kontrollü"
            icon = "🟢"

        if label == "Kur Riski":
            title = "Kur bağımlılığı kontrolü"
            if score >= 55:
                message = (
                    "Portföyde döviz ve yabancı varlık etkisi izlenmeli. "
                    "Kur hareketleri toplam performansı olduğundan fazla etkileyebilir."
                )
            else:
                message = (
                    "Kur etkisi şu an kontrollü görünüyor. "
                    "Ancak yabancı varlık oranı değiştikçe bu skor hızlı yükselebilir."
                )

        elif label == "Konsantrasyon":
            title = "Yoğunlaşma riski"
            if score >= 75:
                message = (
                    "Portföy sınırlı sayıda fon/tema üzerinde yoğunlaşıyor. "
                    "Fon sayısı yüksek görünse bile gerçek çeşitlendirme düşük olabilir."
                )
            else:
                message = (
                    "Konsantrasyon seviyesi izlenebilir düzeyde. "
                    "Yeni fon eklerken aynı temayı tekrar edip etmediğine dikkat edilmeli."
                )

        elif label == "Likidite":
            title = "Çıkış kabiliyeti"
            if score >= 75:
                message = (
                    "Portföyün stres anında hızlı ve düşük maliyetle nakde dönüşmesi zorlaşabilir. "
                    "Satış valörü ve fon tipi dikkatle izlenmeli."
                )
            else:
                message = (
                    "Likidite riski şu an yönetilebilir görünüyor. "
                    "Yine de portföyde hızlı çıkılabilir katman korunmalı."
                )

        elif label == "Tema Riski":
            title = "Tema çakışması"
            if score >= 55:
                message = (
                    "Aynı yatırım teması farklı fonlarda tekrar ediyor olabilir. "
                    "Bu durum sahte çeşitlendirme yaratabilir."
                )
            else:
                message = (
                    "Tema yoğunluğu şu an düşük görünüyor. "
                    "Bu, portföyün farklı risk motorlarına daha dengeli yayıldığını gösterebilir."
                )

        elif label == "Volatilite":
            title = "Oynaklık farkındalığı"
            if score >= 55:
                message = (
                    "Portföy büyüme odaklı ve oynaklığa açık görünüyor. "
                    "Kısa vadeli düşüşlerde davranışsal baskı oluşabilir."
                )
            else:
                message = (
                    "Volatilite riski şu an daha dengeli görünüyor. "
                    "Bu, portföyün stres dönemlerinde daha yönetilebilir olmasına yardımcı olabilir."
                )

        else:
            title = label
            message = item["reason"]

        feed.append(
            {
                "icon": icon,
                "severity": severity,
                "title": title,
                "message": message,
                "score": score,
                "metric": item["main_metric"],
            }
        )

    return feed

def calculate_exposure_summary() -> dict:
    df = load_inputs_with_latest_prices()

    exposure_fields = {
        "USD": "currency_exposure_usd",
        "EUR": "currency_exposure_eur",
        "TL": "currency_exposure_tl",
        "Altın": "gold_exposure",
        "Hisse": "equity_exposure",
        "Yabancı Hisse": "foreign_equity_exposure",
        "Teknoloji": "technology_exposure",
        "Para Piyasası": "money_market_exposure",
    }

    result = {}

    for label, column in exposure_fields.items():
        value = weighted_current_value_average(df, column)

        if value >= 60:
            level = "Yüksek"
        elif value >= 30:
            level = "Orta"
        else:
            level = "Düşük"

        result[label] = {
            "value": round(value, 1),
            "level": level,
        }

    return result

# AI_HOOK:
# Future LLM reasoning layer:
# Explain causal portfolio drivers,
# dominant themes,
# hidden concentration risks,
# and cross-factor relationships
# in natural language.
def calculate_performance_attribution() -> dict:
    df = load_inputs_with_latest_prices()

    # Güncel değer bazlı ağırlık proxy.
    # risk_engine şu an fiyat DB okumadığı için avg_cost bazlı position_cost kullanıyoruz.
    # Bir sonraki adımda bunu gerçek current_value ile portfolio DB üzerinden bağlayacağız.
    total_position = df["current_value"].sum()

    if total_position <= 0:
        return {
            "items": [],
            "insight": "Attribution hesaplamak için yeterli portföy verisi yok.",
        }

    df["weight"] = df["current_value"] / total_position

    usd = (df["weight"] * df["currency_exposure_usd"]).sum()
    tech = (df["weight"] * df["technology_exposure"]).sum()
    gold = (df["weight"] * df["gold_exposure"]).sum()
    commodity = (df["weight"] * df["commodity_exposure"]).sum()
    equity = (df["weight"] * df["equity_exposure"]).sum()
    foreign_equity = (df["weight"] * df["foreign_equity_exposure"]).sum()

    bist = max(equity - foreign_equity, 0)

    raw = {
        "USD Etkisi": max(usd, 0),
        "Global Teknoloji": max(tech, 0),
        "Altın / Emtia": max(gold + commodity, 0),
        "BIST / TL Hisse": max(bist, 0),
        "Fon Seçimi Alfa": 12,
    }

    total = sum(raw.values())

    if total == 0:
        return {
            "items": [],
            "insight": "Attribution hesaplamak için yeterli veri yok.",
        }

    items = []

    for label, value in raw.items():
        contribution = value / total * 100
        items.append(
            {
                "label": label,
                "weight": round(contribution, 1),
            }
        )

    sorted_items = sorted(
        items,
        key=lambda x: x["weight"],
        reverse=True,
    )

    main_driver = sorted_items[0]["label"]

    insight = (
        f"Portföy performansının ana sürücüsü şu anda {main_driver} görünüyor. "
        "Bu analiz kesin getiri ayrıştırması değil; portföyün hangi risk/tema "
        "motorlarından beslendiğini gösteren awareness attribution yaklaşımıdır."
    )

    return {
        "items": sorted_items,
        "insight": insight,
    }


def calculate_liquidity_exit_summary() -> dict:
    df = load_inputs()

    weighted_sell_value = weighted_average(df, "sell_value")
    money_market = weighted_average(df, "money_market_exposure")

    instant_ratio = df[df["sell_value"] <= 1]["portfolio_weight"].sum()
    medium_ratio = df[
        (df["sell_value"] > 1) & (df["sell_value"] <= 2)
    ]["portfolio_weight"].sum()
    slow_ratio = df[df["sell_value"] > 2]["portfolio_weight"].sum()

    liquidity_score = clamp(
        weighted_sell_value * 28
        - money_market * 0.35
        + 25
    )

    if liquidity_score >= 75:
        level = "Kritik"
        insight = (
            "Portföyün stres anında hızlı ve düşük maliyetle nakde dönüşmesi "
            "zorlaşabilir. Satış valörü ve düşük para piyasası oranı dikkat çekiyor."
        )
    elif liquidity_score >= 55:
        level = "İzlenmeli"
        insight = (
            "Likidite riski orta-yüksek seviyede. Ani nakit ihtiyacı doğarsa "
            "bazı fonlarda çıkış süresi davranışsal baskı oluşturabilir."
        )
    else:
        level = "Kontrollü"
        insight = (
            "Likidite görünümü yönetilebilir. Yine de portföyde hızlı çıkılabilir "
            "katmanın korunması faydalı olur."
        )

    return {
        "liquidity_score": liquidity_score,
        "level": level,
        "weighted_sell_value": round(weighted_sell_value, 1),
        "instant_ratio": round(instant_ratio, 1),
        "medium_ratio": round(medium_ratio, 1),
        "slow_ratio": round(slow_ratio, 1),
        "money_market_ratio": round(money_market, 1),
        "insight": insight,
    }

def calculate_theme_exposure_summary() -> list[dict]:
    df = load_inputs_with_latest_prices()

    theme_map = {
        "Teknoloji": "technology_exposure",
        "Bankacılık": "banking_exposure",
        "Savunma": "defense_exposure",
        "Yabancı Hisse": "foreign_equity_exposure",
        "Altın": "gold_exposure",
        "Emtia": "commodity_exposure",
        "Para Piyasası": "money_market_exposure",
        "Blockchain / Metaverse": "blockchain_metaverse_exposure",
    }

    result = []

    for label, column in theme_map.items():
        value = weighted_current_value_average(df, column)

        if value >= 50:
            risk_effect = "Yüksek"
        elif value >= 25:
            risk_effect = "Orta"
        elif label in ["Para Piyasası", "Altın"] and value >= 10:
            risk_effect = "Koruyucu"
        else:
            risk_effect = "Düşük"

        result.append(
            {
                "theme": label,
                "value": round(value, 1),
                "risk_effect": risk_effect,
            }
        )

    result = sorted(
        result,
        key=lambda x: x["value"],
        reverse=True,
    )

    return result

def calculate_portfolio_health() -> list[dict]:
    risk_data = calculate_risk_engine()
    exposure_data = calculate_exposure_summary()
    liquidity_data = calculate_liquidity_exit_summary()
    theme_data = calculate_theme_exposure_summary()

    components = risk_data["components"]

    health = []

    concentration_score = components["concentration"]["score"]
    liquidity_score = liquidity_data["liquidity_score"]
    fx_score = components["currency"]["score"]
    volatility_score = components["volatility"]["score"]

    defensive_layer = (
        exposure_data["Para Piyasası"]["value"]
        + exposure_data["Altın"]["value"] * 0.5
    )

    top_theme = theme_data[0]

    if concentration_score >= 75:
        health.append(
            {
                "area": "Diversification",
                "status": "Zayıf",
                "level": "Kritik",
                "message": "Portföy sınırlı sayıda fon veya temada yoğunlaşıyor.",
            }
        )
    else:
        health.append(
            {
                "area": "Diversification",
                "status": "Yönetilebilir",
                "level": "Kontrollü",
                "message": "Fon dağılımı şu an izlenebilir seviyede.",
            }
        )

    if liquidity_score >= 75:
        health.append(
            {
                "area": "Liquidity Buffer",
                "status": "Düşük",
                "level": "Kritik",
                "message": "Stres anında hızlı çıkış kabiliyeti sınırlı olabilir.",
            }
        )
    else:
        health.append(
            {
                "area": "Liquidity Buffer",
                "status": "Yeterli",
                "level": "Kontrollü",
                "message": "Likidite görünümü şu an yönetilebilir.",
            }
        )

    if fx_score >= 55:
        health.append(
            {
                "area": "FX Balance",
                "status": "Döviz Hassas",
                "level": "İzlenmeli",
                "message": "Kur hareketleri portföy davranışını belirgin etkileyebilir.",
            }
        )
    else:
        health.append(
            {
                "area": "FX Balance",
                "status": "Dengeli",
                "level": "Kontrollü",
                "message": "Kur riski şu an görece kontrollü.",
            }
        )

    if defensive_layer < 20:
        health.append(
            {
                "area": "Defensive Layer",
                "status": "Eksik",
                "level": "İzlenmeli",
                "message": "Para piyasası ve koruyucu katman portföyde düşük görünüyor.",
            }
        )
    else:
        health.append(
            {
                "area": "Defensive Layer",
                "status": "Var",
                "level": "Kontrollü",
                "message": "Portföyde belirli ölçüde koruyucu katman bulunuyor.",
            }
        )

    if volatility_score >= 55:
        health.append(
            {
                "area": "Growth Dependency",
                "status": "Yüksek",
                "level": "İzlenmeli",
                "message": "Portföy büyüme/hisse temasına duyarlı çalışıyor.",
            }
        )
    else:
        health.append(
            {
                "area": "Growth Dependency",
                "status": "Düşük-Orta",
                "level": "Kontrollü",
                "message": "Büyüme teması portföyü aşırı domine etmiyor.",
            }
        )

    health.append(
        {
            "area": "Top Theme",
            "status": top_theme["theme"],
            "level": top_theme["risk_effect"],
            "message": f"En baskın tema %{top_theme['value']} ile {top_theme['theme']}.",
        }
    )

    return health

def calculate_data_quality() -> list[dict]:
    df = load_inputs_with_latest_prices()

    checks = []

    missing_price_count = df["price"].isna().sum()
    checks.append(
        {
            "check": "Fiyat Verisi",
            "status": "OK" if missing_price_count == 0 else "Eksik",
            "level": "Kontrollü" if missing_price_count == 0 else "Kritik",
            "message": (
                "Tüm fonlarda güncel fiyat var."
                if missing_price_count == 0
                else f"{missing_price_count} fon için fiyat verisi eksik."
            ),
        }
    )

    exposure_total = (
        df["currency_exposure_usd"]
        + df["currency_exposure_eur"]
        + df["currency_exposure_tl"]
    )

    broken_exposure_count = (
        (exposure_total < 99)
        | (exposure_total > 101)
    ).sum()

    checks.append(
        {
            "check": "Kur Exposure Toplamı",
            "status": "OK" if broken_exposure_count == 0 else "Kontrol",
            "level": "Kontrollü" if broken_exposure_count == 0 else "İzlenmeli",
            "message": (
                "Tüm fonlarda USD + EUR + TL toplamı yaklaşık 100."
                if broken_exposure_count == 0
                else f"{broken_exposure_count} fonda kur exposure toplamı 100 değil."
            ),
        }
    )

    invalid_position_count = (
        (df["units"] <= 0)
        | (df["avg_cost"] <= 0)
    ).sum()

    checks.append(
        {
            "check": "Pozisyon Verisi",
            "status": "OK" if invalid_position_count == 0 else "Hatalı",
            "level": "Kontrollü" if invalid_position_count == 0 else "Kritik",
            "message": (
                "Tüm fonlarda adet ve maliyet pozitif."
                if invalid_position_count == 0
                else f"{invalid_position_count} fonda adet/maliyet hatalı."
            ),
        }
    )

    latest_price_date = pd.to_datetime(
        df["price_date"],
        errors="coerce",
    ).max()

    if pd.isna(latest_price_date):
        price_age_days = 999
    else:
        price_age_days = (
            pd.Timestamp.today().normalize()
            - latest_price_date.normalize()
        ).days

    checks.append(
        {
            "check": "TEFAS Fiyat Yaşı",
            "status": "Güncel" if price_age_days <= 3 else "Eski",
            "level": "Kontrollü" if price_age_days <= 3 else "İzlenmeli",
            "message": (
                f"Son fiyat tarihi {price_age_days} gün eski."
                if price_age_days < 999
                else "Fiyat tarihi okunamadı."
            ),
        }
    )

    metadata_missing = df[
        [
            "risk_value",
            "sell_value",
            "theme_primary",
        ]
    ].isna().any(axis=1).sum()

    checks.append(
        {
            "check": "Metadata",
            "status": "OK" if metadata_missing == 0 else "Eksik",
            "level": "Kontrollü" if metadata_missing == 0 else "Kritik",
            "message": (
                "Tüm fonlarda temel metadata var."
                if metadata_missing == 0
                else f"{metadata_missing} fonda temel metadata eksik."
            ),
        }
    )

    return checks

# AI_HOOK:
# Future LLM reasoning layer:
# Interpret macro scenarios,
# explain second-order effects,
# identify vulnerable positions,
# and generate strategic portfolio responses.
def run_macro_scenario(
    scenario_name: str,
    shock_percent: float,
) -> dict:

    df = load_inputs_with_latest_prices()

    total_value = df["current_value"].sum()

    if total_value <= 0:

        return {
            "scenario": scenario_name,
            "estimated_impact_pct": 0,
            "estimated_impact_tl": 0,
            "relevant_exposure": 0,
            "sensitivity": 0,
            "comment": "Portfoy degeri hesaplanamadi.",
        }

    config = SCENARIO_CONFIG.get(scenario_name)

    if not config:

        return {
            "scenario": scenario_name,
            "estimated_impact_pct": 0,
            "estimated_impact_tl": 0,
            "relevant_exposure": 0,
            "sensitivity": 0,
            "comment": "Tanimsiz senaryo.",
        }

    weights = df["current_value"] / total_value
    exposure = calculate_factor_exposure(df, scenario_name)
    sensitivity = config.get("sensitivity", 1.0)

    estimated_portfolio_effect = float((
        weights
        * exposure
        * shock_percent
        * sensitivity
    ).sum())

    estimated_tl_effect = (
        total_value
        * estimated_portfolio_effect
        / 100
    )

    return {
        "scenario": scenario_name,
        "estimated_impact_pct": float(round(
            estimated_portfolio_effect,
            2,
        )),
        "estimated_impact_tl": float(round(
            estimated_tl_effect,
            0,
        )),
        "relevant_exposure": round(
            calculate_portfolio_factor_exposure(df, scenario_name),
            1,
        ),
        "sensitivity": sensitivity,
        "comment": config.get("comment", ""),
    }
def calculate_snapshot_change_tracker() -> list[dict]:
    if IS_DEMO_MODE:
        return [
            {
                "metric": "Risk Score",
                "latest": 44,
                "previous": 47,
                "delta": -3,
                "direction": "\u2193",
            },
            {
                "metric": "USD Exposure",
                "latest": 29.7,
                "previous": 31.2,
                "delta": -1.5,
                "direction": "\u2193",
            },
            {
                "metric": "Equity Exposure",
                "latest": 41.5,
                "previous": 39.8,
                "delta": 1.7,
                "direction": "\u2191",
            },
            {
                "metric": "Volatility",
                "latest": 37,
                "previous": 39,
                "delta": -2,
                "direction": "\u2193",
            },
        ]

    with sqlite3.connect(DB_PATH) as conn:

        snapshots_df = pd.read_sql_query(
            """
            SELECT *
            FROM portfolio_snapshots
            ORDER BY snapshot_date ASC
            """,
            conn,
        )

    if len(snapshots_df) < 2:

        return []

    latest = snapshots_df.iloc[-1]
    previous = snapshots_df.iloc[-2]

    metrics = [
        (
            "Risk Score",
            latest["risk_score"],
            previous["risk_score"],
        ),
        (
            "USD Exposure",
            latest["usd_exposure"],
            previous["usd_exposure"],
        ),
        (
            "Equity Exposure",
            latest["equity_exposure"],
            previous["equity_exposure"],
        ),
        (
            "Volatility",
            latest["volatility_score"],
            previous["volatility_score"],
        ),
    ]

    changes = []

    for label, latest_value, previous_value in metrics:

        delta = round(
            latest_value - previous_value,
            1,
        )

        if delta > 0:
            direction = "↑"
        elif delta < 0:
            direction = "↓"
        else:
            direction = "→"

        changes.append(
            {
                "metric": label,
                "latest": round(latest_value, 1),
                "previous": round(previous_value, 1),
                "delta": delta,
                "direction": direction,
            }
        )

    return changes

def calculate_scenario_drivers(
    scenario_name: str,
    shock_percent: float,
) -> pd.DataFrame:

    df = load_inputs_with_latest_prices()

    total_value = df["current_value"].sum()

    if total_value <= 0:
        return pd.DataFrame()

    config = SCENARIO_CONFIG.get(scenario_name)

    if not config:
        return pd.DataFrame()

    df["weight"] = df["current_value"] / total_value
    df["relevant_exposure"] = calculate_factor_exposure(df, scenario_name) * 100
    df["scenario_shock"] = shock_percent
    df["sensitivity"] = config.get("sensitivity", 1.0)

    df["estimated_effect_pct"] = (
        df["weight"]
        * (df["relevant_exposure"] / 100)
        * df["scenario_shock"]
        * df["sensitivity"]
    )

    df["estimated_effect_tl"] = (
        total_value
        * df["estimated_effect_pct"]
        / 100
    )

    result_df = df[
        [
            "fund_code",
            "scenario_shock",
            "relevant_exposure",
            "sensitivity",
            "estimated_effect_pct",
            "estimated_effect_tl",
            "theme_primary",
        ]
    ].copy()

    result_df = result_df.sort_values(
        by="estimated_effect_tl",
        ascending=False,
    )

    return result_df
if __name__ == "__main__":
    result = calculate_risk_engine()

    print("\n========== FONPILOT K07 RISK ENGINE ==========\n")
    print(f"Genel Risk Skoru: {result['overall_score']} / 100")
    print(f"Seviye: {result['overall_level']}")
    print("-" * 50)

    for item in result["components"].values():
        print(f"{item['label']}: {item['score']} / 100 · {item['level']}")
        print(f"  {item['main_metric']}")
        print(f"  {item['reason']}")
        print("-" * 50)
