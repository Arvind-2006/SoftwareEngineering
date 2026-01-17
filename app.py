import psycopg2


from flask import Flask, render_template, request
from datetime import datetime

conn = psycopg2.connect(
    host="localhost",
    database="amds",
    user="postgres",
    password="Arvind@88000"
)

cursor = conn.cursor()



app = Flask(__name__)

# Temporary storage (simulation)
prescriptions = {}
logs = []

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
    cursor.execute("SELECT patient_id, medicine, timestamp, status FROM logs")
    logs = cursor.fetchall()
    return render_template('admin.html', logs=logs)


from psycopg2 import Error

@app.route('/add_prescription', methods=['POST'])
def add_prescription():
    try:
        patient_id = request.form['patient_id']
        medicine = request.form['medicine']
        dosage = request.form['dosage']

        cursor.execute("""
            INSERT INTO prescriptions (patient_id, medicine, dosage)
            VALUES (%s, %s, %s)
        """, (patient_id, medicine, dosage))

        conn.commit()
        return "Prescription added successfully"

    except Error as e:
        conn.rollback()   
        return f"Database error: {e}"


@app.route('/get_medicine', methods=['POST'])
def get_medicine():
    patient_id = request.form['patient_id']

    cursor.execute("""
        SELECT prescription_id, medicine, dosage, dispensed
        FROM prescriptions
        WHERE patient_id = %s
    """, (patient_id,))

    result = cursor.fetchone()

    if not result:
        return render_template('patient.html', error="No prescription found")

    prescription_id, medicine, dosage, dispensed = result

    if dispensed:
        return render_template('patient.html', error="Dose already taken")

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

    return render_template(
        'patient.html',
        message="Medicine Dispensed Successfully",
        medicine=medicine,
        dosage=dosage
    )


@app.route('/view_prescriptions/<patient_id>')
def view_prescriptions(patient_id):
    cursor.execute("""
        SELECT prescription_id, medicine, dosage, dispensed
        FROM prescriptions
        WHERE patient_id = %s
    """, (patient_id,))
    patient_prescriptions = cursor.fetchall()
    return render_template('view_prescriptions.html', prescriptions=patient_prescriptions)
@app.route('/view_logs')
def view_logs():    
    return render_template('view_logs.html', logs=logs)



if __name__ == '__main__':
    app.run(debug=True)