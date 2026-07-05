import yfinance as yf
from datetime import datetime 
import math

def get_market_pulse():

    assets = {
        "USDTRY": "USDTRY=X",
        "EURTRY": "EURTRY=X",
        "GOLD": "GC=F",

        "DXY": "DX-Y.NYB",
        "BTC": "BTC-USD",

        "NASDAQ100": "^QQQ",
        "SP500": "SPY",
        "BIST100": "XU100.IS",

        "US10Y": "^TNX",

        "QQQM": "QQQM",
        "SOXQ": "SOXQ",
    }

    result = {}

    for name, ticker in assets.items():

        data = yf.Ticker(ticker)

        hist = data.history(period="2d")

        if len(hist) < 2:
            continue

        current_price = float(hist["Close"].iloc[-1])

        previous_price = float(hist["Close"].iloc[-2])

        if (
            math.isnan(current_price)
            or math.isnan(previous_price)
            or previous_price == 0
        ):
            continue



        daily_change_pct = (
            (
                current_price
                - previous_price
            )
            / previous_price
        ) * 100

        result[name] = {
            "price": round(current_price, 4),
            "change_pct": round(
                daily_change_pct,
                2,
            ),
        }
    result["updated_at"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M"
)
    return result


if __name__ == "__main__":

    print(
        get_market_pulse()
    )