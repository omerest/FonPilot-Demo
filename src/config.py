from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DATA_DIR = ROOT_DIR / "sample_data"

FONPILOT_MODE = "demo"
IS_DEMO_MODE = True

DB_PATH = DATA_DIR / "fonpilot.db"
PORTFOLIO_CSV_PATH = SAMPLE_DATA_DIR / "sample_portfolio_funds.csv"
METADATA_CSV_PATH = SAMPLE_DATA_DIR / "sample_fund_metadata.csv"

REFRESH_HOUR = 20
REFRESH_MINUTE = 0
