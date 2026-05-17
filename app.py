from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "hospital123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Satya%402006@localhost/hospital_db'

db = SQLAlchemy(app)

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
            status='Pending'
        )
        db.session.add(new_appointment)
        db.session.commit()
        return redirect('/billing')
    return render_template('book_appointment.html', doctors=doctors)

@app.route('/my_appointments')
def my_appointments():
    if 'patient_id' not in session:
        return redirect('/login')
    appointments = db.session.query(Appointment, Doctor).join(
        Doctor, Appointment.doctor_id == Doctor.id
    ).filter(Appointment.patient_id == session['patient_id']).all()
    return render_template('my_appointments.html', appointments=appointments)
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    status = db.Column(db.String(20))
@app.route('/billing', methods=['GET', 'POST'])
def billing():

    if request.method == 'POST':

        patient_name = request.form['patient_name']

        doctor_fee = int(request.form['doctor_fee'])

        medicine_fee = int(request.form['medicine_fee'])

        room_fee = int(request.form['room_fee'])

        total_amount = (
            doctor_fee +
            medicine_fee +
            room_fee
        )

        payment_status = request.form['payment_status']

        query = """
        INSERT INTO billing
        (
            patient_name,
            doctor_fee,
            medicine_fee,
            room_fee,
            total_amount,
            payment_status
        )

        VALUES
        (
            :patient_name,
            :doctor_fee,
            :medicine_fee,
            :room_fee,
            :total_amount,
            :payment_status
        )
        """

        db.session.execute(
            db.text(query),
            {
                "patient_name": patient_name,
                "doctor_fee": doctor_fee,
                "medicine_fee": medicine_fee,
                "room_fee": room_fee,
                "total_amount": total_amount,
                "payment_status": payment_status
            }
        )

        db.session.commit()

        return redirect('/my_appointments')

    return render_template('billing.html')
if __name__ == '__main__':
    app.run(debug=True)