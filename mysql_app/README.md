# Hospital Management — MySQL edition

This is a separate MySQL-compatible browser app. The original PostgreSQL project at the repository root is intentionally unchanged.

## What it does
- Connects to an existing MySQL database (default name: `Hospital_Management`).
- Discovers existing tables and columns using MySQL metadata.
- Shows a dashboard with per-table record counts.
- Browses records in pages of 50.
- Provides a generic add-record form based on each table's actual columns.
- Includes a database health check at `/health`.

It does **not** create, drop, rename, or alter tables. It does not include delete or edit actions.

## Run locally (Windows)
1. Install Python 3.10+ and MySQL Server. Make sure your existing MySQL server is running.
2. Open a terminal in the `mysql_app` folder.
3. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to a new file named `.env`. Enter your own MySQL username and password there. Keep `.env` private and never commit it.
6. Start the app:
   ```powershell
   python app.py
   ```
7. Open http://127.0.0.1:5000 in your browser. Visit http://127.0.0.1:5000/health to test the connection.

## Important
The generic interface is intentionally schema-aware, but it cannot know the meaning of every field or automatically handle every foreign-key workflow. Review the forms and constraints before entering data. Use sample/test data only. This starter app has no authentication, authorization, audit trail, CSRF protection, or production health-data safeguards. Keep it on your own computer; do not expose it to the public internet or enter real patient information.
