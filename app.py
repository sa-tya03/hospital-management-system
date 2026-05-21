from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "hospital123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Satya%402006@localhost/hospital_db'

db = SQLAlchemy(app)
class Billing(db.Model):
    __tablename__ = 'billing'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    doctor_fee = db.Column(db.Integer, default=0)
    medicine_fee = db.Column(db.Integer, default=0)
    room_fee = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Integer, default=0)
    payment_status = db.Column(db.String(20), default='Unpaid')
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    status = db.Column(db.String(20))
# Patient Model
class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(15))
    age = db.Column(db.Integer)
# Doctor Model
class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    consultation_fee = db.Column(db.Integer, default=500) 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']
        age = request.form['age']
        new_patient = Patient(name=name, email=email,
                             password=password, phone=phone, age=age)
        db.session.add(new_patient)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        patient = Patient.query.filter_by(email=email).first()
        if patient and check_password_hash(patient.password, password):
            session['patient_id'] = patient.id
            session['patient_name'] = patient.name
            return redirect('/dashboard')
        else:
            return "Invalid credentials! <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'patient_id' not in session:
        return redirect('/login')
    doctors = Doctor.query.all()
    return render_template('dashboard.html', 
                         name=session['patient_name'],
                         doctors=doctors)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'patient_id' not in session:
        return redirect('/login')
    doctors = Doctor.query.all()
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        date = request.form['date']
        time = request.form['time']
        new_appointment = Appointment(
            patient_id=session['patient_id'],
            doctor_id=doctor_id,
            date=date,
            time=time,
            status='Confirmed'
        )
        db.session.add(new_appointment)
        db.session.commit()
        doctor = Doctor.query.get(doctor_id)
        doctor_fee   = doctor.consultation_fee
        medicine_fee = 200
        room_fee     = 300
        total        = doctor_fee + medicine_fee + room_fee
        bill = Billing(
            patient_id     = session['patient_id'],
            appointment_id = new_appointment.id,
            doctor_fee     = doctor_fee,
            medicine_fee   = medicine_fee,
            room_fee       = room_fee,
            total_amount   = total,
            payment_status = 'Unpaid')
        db.session.add(bill)
        db.session.commit()
        return redirect('/my_appointments')
    return render_template('book_appointment.html', doctors=doctors)
@app.route('/my_appointments')
def my_appointments():
    if 'patient_id' not in session:
        return redirect('/login')
    appointments = db.session.query(Appointment, Doctor).join(
        Doctor, Appointment.doctor_id == Doctor.id
    ).filter(Appointment.patient_id == session['patient_id']).all()
    return render_template('my_appointments.html', appointments=appointments)
@app.route('/view_bill')
def view_bill():
    if 'patient_id' not in session:
        return redirect('/login')
    bills = db.session.query(Billing, Appointment).join(
        Appointment, Billing.appointment_id == Appointment.id
    ).filter(Billing.patient_id == session['patient_id']).all()
    return render_template('view_bill.html', bills=bills)

@app.route('/pay_bill/<int:bill_id>', methods=['POST'])
def pay_bill(bill_id):
    bill = Billing.query.get(bill_id)
    bill.payment_status = "Paid"
    db.session.commit()
    return redirect('/view_bill')
if __name__ == '__main__':
    app.run(debug=True)
