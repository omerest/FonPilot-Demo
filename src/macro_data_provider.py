import os
from datetime import datetime

import requests


TCMB_EVDS_URL = "https://evds2.tcmb.gov.tr/service/evds/"
DEFAULT_POLICY_RATE_SERIES = "TP.PPK.POLICY"


def fetch_tcmb_policy_rate() -> dict:
    api_key = os.getenv("TCMB_EVDS_API_KEY", "").strip()
    policy_rate_series = os.getenv(
        "TCMB_POLICY_RATE_SERIES",
        DEFAULT_POLICY_RATE_SERIES,
    ).strip()

    if not api_key:
        return {
            "value": None,
            "source": "TCMB EVDS",
            "status": "unavailable",
            "message": "TCMB_EVDS_API_KEY tanimli degil.",
            "updated_at": None,
        }

    params = {
        "series": policy_rate_series,
        "startDate": "01-01-2024",
        "endDate": datetime.now().strftime("%d-%m-%Y"),
        "type": "json",
        "key": api_key,
    }

    try:
        response = requests.get(
            TCMB_EVDS_URL,
            params=params,
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("items", [])

        for row in reversed(rows):
            raw_value = row.get(policy_rate_series)
            if raw_value not in [None, ""]:
                return {
                    "value": float(str(raw_value).replace(",", ".")),
                    "source": "TCMB EVDS",
                    "status": "ok",
                    "message": "TCMB EVDS politika faizi verisi alindi.",
                    "updated_at": row.get("Tarih"),
                }

        return {
            "value": None,
            "source": "TCMB EVDS",
            "status": "unavailable",
            "message": "TCMB EVDS yanitinda politika faizi degeri bulunamadi.",
            "updated_at": None,
        }

    except Exception as exc:
        return {
            "value": None,
            "source": "TCMB EVDS",
            "status": "error",
            "message": f"TCMB EVDS verisi alinamadi: {exc}",
            "updated_at": None,
        }
