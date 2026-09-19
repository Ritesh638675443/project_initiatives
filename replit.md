# SIGMA Abstract Submission Portal

Pure Streamlit portal for submitting, storing, and administering SIGMA Domain Mini Project abstracts.

## Run & Operate

- `streamlit run app.py` — run the Streamlit application
- `python -m py_compile app.py database.py storage.py utils.py` — check Python syntax

## Stack

- Python, Streamlit, SQLite, pandas, openpyxl
- The root `app.py` is the source of truth for the user-facing application.

## Where things live

- `app.py` — Streamlit pages, forms, dashboard, and navigation
- `database.py` — SQLite schema and data access
- `storage.py` — local PDF storage abstraction
- `utils.py` — validation, exports, filenames, and shared constants
- `data/` — generated SQLite database and uploaded PDFs (ignored by git)
- `requirements.txt` — Streamlit deployment dependencies

## Architecture decisions

- Metadata and uploaded files are intentionally separated so cloud storage can be added later.
- The app uses Streamlit session state for admin authentication as requested for the prototype.
- Duplicate submissions are enforced in SQLite with a case-insensitive team/domain unique index.
- Uploads are validated by extension, size, and PDF magic bytes before storage.

## Product

Students submit one SIGMA mini-project abstract per team/domain. Coordinators can filter submissions, inspect members, preview/download PDFs, and export Excel, CSV, and ZIP archives.

## User preferences
- Keep the application purely Streamlit and easy to deploy.

## Gotchas

- Do not commit `.streamlit/secrets.toml`; use Streamlit Cloud secrets for deployed admin credentials.
- Local file storage is prototype-friendly but not durable across all hosted rebuilds; use `storage.py` as the migration seam.

## Pointers

- See the `streamlit` skill for Streamlit development guidance.
