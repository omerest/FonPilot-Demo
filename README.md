# FonPilot Demo

AI Supported TEFAS Investment Intelligence Platform

## Purpose

FonPilot Demo is a public, read-only product showcase.

It is not a real portfolio. It uses anonymized sample data only and does not include private portfolio positions, costs, SQLite databases, backups, baselines, logs, or personal Excel files.

## Demo Mode

Demo mode is the default behavior in this repository.

```text
FONPILOT_MODE=demo
```

If the variable is not set, the app still defaults to demo mode.

## Run Locally

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

Use `app.py` as the entrypoint.

Set this secret or environment variable in the cloud settings:

```text
FONPILOT_MODE=demo
```

## Included Data

Safe demo files:

```text
sample_data/sample_portfolio_funds.csv
sample_data/sample_fund_metadata.csv
```

## Disabled In Demo

- Portfolio Editor writes
- Metadata Editor writes
- Snapshot Save
- TEFAS Refresh writes
- Scheduler
- Backup engine
- Local database writes

## Not Included

- `data/`
- `fonpilot.db`
- `portfolio_funds.csv`
- `fund_metadata.csv`
- backups
- baselines
- logs
- personal Excel files
