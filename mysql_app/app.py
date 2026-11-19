from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-this-local-development-key")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

def connection():
    required = ("MYSQL_HOST", "MYSQL_USER", "MYSQL_DATABASE")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError("Set " + ", ".join(missing) + " in mysql_app/.env")
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE"),
        connection_timeout=5,
    )

def quote_identifier(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"

def get_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME", (os.getenv("MYSQL_DATABASE"),))
    rows = [row[0] for row in cur.fetchall()]
    cur.close()
    return rows

def get_columns(conn, table):
    cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
                          EXTRA, CHARACTER_MAXIMUM_LENGTH
                   FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION""",
                (os.getenv("MYSQL_DATABASE"), table))
    rows = cur.fetchall()
    cur.close()
    return rows

@app.template_filter("display_value")
def display_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return "[binary data]"
    return value

@app.get("/")
def dashboard():
    with connection() as conn:
        tables = get_tables(conn)
        stats = []
        cur = conn.cursor()
        for table in tables:
            cur.execute("SELECT COUNT(*) FROM " + quote_identifier(table))
            stats.append({"name": table, "count": cur.fetchone()[0]})
        cur.close()
    return render_template("dashboard.html", tables=stats, database=os.getenv("MYSQL_DATABASE"))

@app.get("/table/<table>")
def view_table(table):
    with connection() as conn:
        if table not in get_tables(conn):
            abort(404)
        columns = get_columns(conn, table)
        page = max(1, request.args.get("page", 1, type=int))
        per_page = 50
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) FROM " + quote_identifier(table))
        total = cur.fetchone()["COUNT(*)"]
        cur.execute("SELECT * FROM " + quote_identifier(table) + " LIMIT %s OFFSET %s", (per_page, (page - 1) * per_page))
        rows = cur.fetchall()
        cur.close()
    return render_template("table.html", table=table, columns=columns, rows=rows,
                           page=page, pages=max(1, (total + per_page - 1) // per_page), total=total)

@app.route("/table/<table>/add", methods=["GET", "POST"])
def add_record(table):
    with connection() as conn:
        if table not in get_tables(conn):
            abort(404)
        columns = get_columns(conn, table)
    writable = [c for c in columns if "auto_increment" not in (c["EXTRA"] or "").lower()
                and c["COLUMN_DEFAULT"] is None and c["IS_NULLABLE"] == "NO"
                or c["IS_NULLABLE"] == "YES"]
    writable = [c for c in writable if "auto_increment" not in (c["EXTRA"] or "").lower()
                and c["DATA_TYPE"] not in ("blob", "longblob", "mediumblob", "tinyblob", "geometry")]
    if request.method == "POST":
        names, values = [], []
        for col in writable:
            name = col["COLUMN_NAME"]
            value = request.form.get(name, "").strip()
            if value == "" and col["IS_NULLABLE"] == "YES":
                continue
            if value == "" and col["COLUMN_DEFAULT"] is not None:
                continue
            if value == "" and col["IS_NULLABLE"] == "NO":
                flash(f"{name} is required.", "error")
                return render_template("add.html", table=table, columns=writable), 400
            names.append(quote_identifier(name))
            values.append(value)
        if not names:
            flash("No values supplied.", "error")
            return render_template("add.html", table=table, columns=writable), 400
        try:
            with connection() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO " + quote_identifier(table) + " (" + ", ".join(names) + ") VALUES (" + ", ".join(["%s"] * len(values)) + ")", values)
                conn.commit()
                cur.close()
            flash("Record added.", "success")
            return redirect(url_for("view_table", table=table))
        except mysql.connector.Error:
            app.logger.exception("Insert failed")
            flash("Could not add this record. Check required fields, data types, and unique constraints.", "error")
    return render_template("add.html", table=table, columns=writable)

@app.get("/health")
def health():
    try:
        with connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
        return {"status": "ok", "database": os.getenv("MYSQL_DATABASE")}
    except Exception:
        app.logger.exception("Database health check failed")
        return {"status": "error", "database": "unavailable"}, 503

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
