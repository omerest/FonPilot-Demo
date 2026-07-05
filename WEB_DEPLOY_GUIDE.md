# FonPilot Demo Web Deploy Guide

## Recommended Host

Use Streamlit Community Cloud for the first public demo.

## Entrypoint

```text
app.py
```

## Required Mode

Demo mode is forced in this repository.

```text
FONPILOT_MODE=demo
```

The app uses only `sample_data/` files. It does not require `data/` or a SQLite database for the public demo.

## Deploy Steps

1. Create a new GitHub repository named `FonPilot-Demo`.
2. Commit only the files in this demo folder.
3. Do not copy `data/`, databases, backups, baselines, logs, or personal Excel files.
4. Connect the repository to Streamlit Community Cloud.
5. Set the app entrypoint to `app.py`.
6. Optionally add `FONPILOT_MODE=demo` in app settings/secrets for clarity.
7. Deploy.

## Included Data

```text
sample_data/sample_portfolio_funds.csv
sample_data/sample_fund_metadata.csv
```

These files are anonymous demo data. They are not real portfolio data.

## Disabled / Not Included

- Portfolio Editor writes
- Metadata Editor writes
- Snapshot Save
- TEFAS Refresh writes
- Scheduler
- Backup engine
- SQLite database
- `data/`
- baseline JSON
- log files
- personal Excel files

## Public Demo Checklist

- Confirm `sample_data/` contains only anonymous demo rows.
- Confirm no `data/` folder exists in the demo repository.
- Confirm no `*.db`, `*.sqlite`, `*.log`, or personal Excel files exist.
- Run locally:

```powershell
streamlit run app.py
```

- Verify dashboard opens and editor/write sections are hidden.
