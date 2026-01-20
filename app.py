import psycopg2

from flask import Flask, render_template, request
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="amds",
        user="postgres",
        password="Arvind@88000"
    )

app = Flask(__name__)

# Temporary storage (simulation)
prescriptions = {}


@app.route('/')
def home():
    return "AMDS Server Running"

@app.route('/doctor')
def doctor():
    return render_template('doctor.html')

@app.route('/patient')
def patient():
    return render_template('patient.html')

@app.route('/admin')
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT patient_id, medicine, timestamp, status 
        FROM logs
    """)
    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin.html', logs=logs)



from psycopg2 import Error

@app.route('/add_prescription', methods=['POST'])
def add_prescription():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO prescriptions (patient_id, medicine, dosage)
            VALUES (%s, %s, %s)
        """, (
            request.form['patient_id'],
            request.form['medicine'],
            request.form['dosage']
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return "Prescription added successfully"

    except Exception as e:
        if conn:
            conn.rollback()
        return f"Database error: {e}"


@app.route('/get_medicine', methods=['POST'])
def get_medicine():
    patient_id = request.form['patient_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prescription_id, medicine, dosage, dispensed
        FROM prescriptions
        WHERE patient_id = %s AND dispensed = FALSE
        LIMIT 1
    """, (patient_id,))

    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        return render_template('patient.html', error="No pending prescription")

    prescription_id, medicine, dosage, dispensed = result

    cursor.execute("""
        UPDATE prescriptions
        SET dispensed = TRUE
        WHERE prescription_id = %s
    """, (prescription_id,))

    cursor.execute("""
        INSERT INTO logs (patient_id, medicine, timestamp, status)
        VALUES (%s, %s, NOW(), %s)
    """, (patient_id, medicine, "Dispensed"))

    conn.commit()

    cursor.close()
    conn.close()

    return render_template(
        'patient.html',
        message="Medicine Dispensed Successfully",
        medicine=medicine,
        dosage=dosage
    )


@app.route('/view_prescriptions/<patient_id>')
def view_prescriptions(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prescription_id, medicine, dosage, dispensed
        FROM prescriptions
        WHERE patient_id = %s
    """, (patient_id,))

    patient_prescriptions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'view_prescriptions.html',
        prescriptions=patient_prescriptions
    )

# @app.route('/view_logs')
# def view_logs():    
#     return render_template('view_logs.html', logs=logs)



if __name__ == '__main__':
    app.run(debug=True)