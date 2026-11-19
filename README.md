# Hospital Management web app (Flask + PostgreSQL)

A small browser-based frontend and Python backend for the hospital SQL database in `sql/schema.sql`. It includes a dashboard, patient search/add form, appointment list, and a database health endpoint. Run from Visual Studio Code (VS Code) or a terminal.

## Requirements

- Python 3.10+
- PostgreSQL with the existing `hospital` schema (`departments`, `doctors`, `patients`, `rooms`, `appointments`, and `admissions` tables at minimum)

The app connects to the existing PostgreSQL database; it does not create, drop, or migrate tables. Keep your database and credentials private.

## Setup in VS Code

1. Open this repository folder in VS Code. Install the Microsoft Python extension.
2. Open the integrated terminal and create a virtual environment:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install packages and prepare environment configuration:
   ```bash
   pip install -r requirements.txt
   ```
   Copy `.env.example` to `.env`, then set `DATABASE_URL` to your PostgreSQL connection. Example:
   `postgresql://postgres:your_password@localhost:5432/hospital_management`
4. In VS Code, choose the virtual environment as the Python interpreter, then press **F5** and select **Flask: Hospital Management**. Alternatively, run:
   ```bash
   python app.py
   ```
5. Open `http://127.0.0.1:5000`. Check `http://127.0.0.1:5000/health` to verify the database connection.

If you have not created the SQL database yet, follow the database setup instructions in the repository's SQL project README and run its schema and seed scripts first. Do not run schema scripts against a production database without a backup and review.

## Database and security notes

The app expects the PostgreSQL schema named `hospital` and uses parameterized SQL for form input. Development mode is off by default. Change `FLASK_SECRET_KEY` to a long random value and do not commit `.env`. This demo does not implement login, roles, audit logging, or production health-data compliance; do not expose it publicly or enter real patient information until those safeguards are implemented.
