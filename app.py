from __future__ import annotations

import os
from datetime import date

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-only-change-me')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError('Set DATABASE_URL in your .env file before starting the app.')
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.get('/')
def dashboard():
    with get_connection() as conn:
        stats = {
            'patients': conn.execute('SELECT COUNT(*) AS count FROM hospital.patients').fetchone()['count'],
            'doctors': conn.execute('SELECT COUNT(*) AS count FROM hospital.doctors WHERE is_active').fetchone()['count'],
            'appointments': conn.execute("SELECT COUNT(*) AS count FROM hospital.appointments WHERE status = 'scheduled' AND appointment_at >= CURRENT_TIMESTAMP").fetchone()['count'],
            'inpatients': conn.execute('SELECT COUNT(*) AS count FROM hospital.admissions WHERE discharged_at IS NULL').fetchone()['count'],
        }
        appointments = conn.execute('''
            SELECT a.appointment_at,
                   p.first_name || ' ' || p.last_name AS patient,
                   d.first_name || ' ' || d.last_name AS doctor,
                   dep.department_name, a.status
            FROM hospital.appointments a
            JOIN hospital.patients p USING (patient_id)
            JOIN hospital.doctors d USING (doctor_id)
            JOIN hospital.departments dep USING (department_id)
            WHERE a.appointment_at >= CURRENT_TIMESTAMP
            ORDER BY a.appointment_at LIMIT 8
        ''').fetchall()
        inpatients = conn.execute('''
            SELECT p.first_name || ' ' || p.last_name AS patient,
                   r.room_number, d.first_name || ' ' || d.last_name AS doctor,
                   ad.admitted_at
            FROM hospital.admissions ad
            JOIN hospital.patients p USING (patient_id)
            JOIN hospital.rooms r USING (room_id)
            JOIN hospital.doctors d ON d.doctor_id = ad.attending_doctor_id
            WHERE ad.discharged_at IS NULL ORDER BY ad.admitted_at LIMIT 8
        ''').fetchall()
    return render_template('dashboard.html', stats=stats, appointments=appointments, inpatients=inpatients)


@app.get('/patients')
def patients():
    query = request.args.get('q', '').strip()
    with get_connection() as conn:
        rows = conn.execute('''
            SELECT patient_id, first_name, last_name, date_of_birth, phone, email
            FROM hospital.patients
            WHERE (%s = '' OR first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s)
            ORDER BY last_name, first_name LIMIT 200
        ''', (query, f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    return render_template('patients.html', patients=rows, query=query)


@app.post('/patients')
def add_patient():
    data = {key: request.form.get(key, '').strip() for key in ('first_name', 'last_name', 'date_of_birth', 'phone', 'email')}
    if not data['first_name'] or not data['last_name'] or not data['date_of_birth']:
        flash('First name, last name, and date of birth are required.', 'error')
        return redirect(url_for('patients'))
    try:
        birth_date = date.fromisoformat(data['date_of_birth'])
        if birth_date > date.today():
            raise ValueError
        with get_connection() as conn:
            conn.execute('''INSERT INTO hospital.patients (first_name, last_name, date_of_birth, phone, email)
                            VALUES (%s, %s, %s, NULLIF(%s, ''), NULLIF(%s, ''))''',
                         (data['first_name'], data['last_name'], birth_date, data['phone'], data['email'] or None))
        flash('Patient added successfully.', 'success')
    except ValueError:
        flash('Enter a valid date of birth that is not in the future.', 'error')
    except psycopg.errors.UniqueViolation:
        flash('That email address is already in use.', 'error')
    return redirect(url_for('patients'))


@app.get('/appointments')
def appointments():
    with get_connection() as conn:
        rows = conn.execute('''
            SELECT a.appointment_at, p.first_name || ' ' || p.last_name AS patient,
                   d.first_name || ' ' || d.last_name AS doctor, dep.department_name,
                   a.reason, a.status
            FROM hospital.appointments a
            JOIN hospital.patients p USING (patient_id)
            JOIN hospital.doctors d USING (doctor_id)
            JOIN hospital.departments dep USING (department_id)
            ORDER BY a.appointment_at DESC LIMIT 200
        ''').fetchall()
    return render_template('appointments.html', appointments=rows)


@app.get('/health')
def health():
    try:
        with get_connection() as conn:
            conn.execute('SELECT 1')
        return {'status': 'ok', 'database': 'connected'}
    except Exception:
        app.logger.exception('Database health check failed')
        return {'status': 'error', 'database': 'unavailable'}, 503


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')
