from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import os

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Templates directory: {TEMPLATE_DIR}")
print(f"📁 Templates exist: {os.path.exists(TEMPLATE_DIR)}")

if os.path.exists(TEMPLATE_DIR):
    print(f"📄 Files in templates: {os.listdir(TEMPLATE_DIR)}")

# Initialize Flask app with absolute template path
app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# ==================== SQLITE DATABASE ====================
# Using SQLite - simple file-based database, no MySQL needed
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(f"🗄️ Using SQLite database at: {os.path.join(BASE_DIR, 'healthcare.db')}")

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page'

db.init_app(app)

# ==================== DATABASE MODELS ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='patient')
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class Specialization(db.Model):
    __tablename__ = 'specializations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    specialization_id = db.Column(db.Integer, db.ForeignKey('specializations.id'))
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Float, default=500)
    bio = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='doctor_profile')
    specialization = db.relationship('Specialization', backref='doctors')

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_dt = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_appointments')
    doctor = db.relationship('Doctor', foreign_keys=[doctor_id], backref='appointments')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== CREATE TABLES AND SEED DATA ====================

def create_database():
    """SQLite doesn't need database creation"""
    print("✅ SQLite database is ready (file-based, no setup needed)")
    pass

# Call the function (does nothing but keeps compatibility)
create_database()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ All tables created fresh!")
    
    specializations = ['Cardiologist', 'Neurologist', 'Dermatologist', 'Pediatrician', 'Orthopedic', 'General Physician']
    for spec_name in specializations:
        db.session.add(Specialization(name=spec_name))
    db.session.commit()
    print("✅ Specializations added")
    
    admin = User(
        name='Admin User',
        email='admin@healthbook.com',
        password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin created: admin@healthbook.com / admin123")
    
    doctors_data = [
        ('Sarah Johnson', 'dr.sarah@healthbook.com', 'Cardiologist', 'MD, FACC', 12, 800, 'Experienced cardiologist with expertise in preventive cardiology.'),
        ('Michael Chen', 'dr.chen@healthbook.com', 'Neurologist', 'MD, PhD', 8, 1000, 'Neurology specialist focusing on headaches and movement disorders.'),
        ('Emily Rodriguez', 'dr.emily@healthbook.com', 'Dermatologist', 'MD, FAAD', 6, 700, 'Dermatology specialist in medical and cosmetic dermatology.'),
        ('James Wilson', 'dr.james@healthbook.com', 'Pediatrician', 'MD, FAAP', 10, 600, 'Compassionate pediatrician caring for children of all ages.'),
    ]
    
    for name, email, spec_name, qual, exp, fee, bio in doctors_data:
        user = User(
            name=name,
            email=email,
            password_hash=bcrypt.generate_password_hash('doctor123').decode('utf-8'),
            role='doctor'
        )
        db.session.add(user)
        db.session.commit()
        
        spec = Specialization.query.filter_by(name=spec_name).first()
        doctor = Doctor(
            user_id=user.id,
            specialization_id=spec.id,
            qualification=qual,
            experience_years=exp,
            consultation_fee=fee,
            bio=bio
        )
        db.session.add(doctor)
    db.session.commit()
    print("✅ 4 sample doctors created")
    print("✅ Database setup complete!")

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            role='patient'
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('my_appointments'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# ==================== PATIENT ROUTES ====================

@app.route('/appointments')
@login_required
def my_appointments():
    if current_user.role != 'patient':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.appointment_dt.desc()).all()
    return render_template('list.html', appointments=appointments, now=datetime.now())

@app.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if current_user.role != 'patient':
        flash('Only patients can book appointments', 'danger')
        return redirect(url_for('index'))
    
    doctors = Doctor.query.all()
    
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_dt = request.form.get('appointment_dt')
        reason = request.form.get('reason')
        
        if not doctor_id:
            flash('Please select a doctor', 'danger')
            return redirect(url_for('book_appointment'))
        
        if not appointment_dt:
            flash('Please select appointment date and time', 'danger')
            return redirect(url_for('book_appointment'))
        
        try:
            appointment_datetime = datetime.strptime(appointment_dt, '%Y-%m-%dT%H:%M')
            
            if appointment_datetime <= datetime.now():
                flash('Appointment must be in the future', 'danger')
                return redirect(url_for('book_appointment'))
            
            new_appointment = Appointment(
                patient_id=current_user.id,
                doctor_id=doctor_id,
                appointment_dt=appointment_datetime,
                reason=reason,
                status='pending'
            )
            db.session.add(new_appointment)
            db.session.commit()
            
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('my_appointments'))
            
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('book_appointment'))
    
    return render_template('book.html', doctors=doctors, now=datetime.now())

@app.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != current_user.id:
        flash('You cannot edit this appointment', 'danger')
        return redirect(url_for('my_appointments'))
    
    if appointment.status != 'pending':
        flash('Only pending appointments can be edited', 'danger')
        return redirect(url_for('my_appointments'))
    
    doctors = Doctor.query.all()
    
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_dt = request.form.get('appointment_dt')
        reason = request.form.get('reason')
        
        if not doctor_id:
            flash('Please select a doctor', 'danger')
            return redirect(url_for('edit_appointment', appointment_id=appointment_id))
        
        if not appointment_dt:
            flash('Please select appointment date and time', 'danger')
            return redirect(url_for('edit_appointment', appointment_id=appointment_id))
        
        try:
            appointment_datetime = datetime.strptime(appointment_dt, '%Y-%m-%dT%H:%M')
            
            if appointment_datetime <= datetime.now():
                flash('Appointment must be in the future', 'danger')
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            appointment.doctor_id = doctor_id
            appointment.appointment_dt = appointment_datetime
            appointment.reason = reason
            
            db.session.commit()
            
            flash('Appointment updated successfully!', 'success')
            return redirect(url_for('my_appointments'))
            
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('edit_appointment', appointment_id=appointment_id))
    
    formatted_datetime = appointment.appointment_dt.strftime('%Y-%m-%dT%H:%M') if appointment.appointment_dt else ''
    
    return render_template('edit_appointment.html', 
                         appointment=appointment, 
                         doctors=doctors, 
                         formatted_datetime=formatted_datetime,
                         now=datetime.now())

@app.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != current_user.id:
        flash('You cannot cancel this appointment', 'danger')
        return redirect(url_for('my_appointments'))
    
    if appointment.appointment_dt <= datetime.now():
        flash('Cannot cancel past appointments', 'danger')
        return redirect(url_for('my_appointments'))
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully', 'success')
    return redirect(url_for('my_appointments'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    total_users = User.query.count()
    total_appointments = Appointment.query.count()
    total_doctors = Doctor.query.count()
    pending_appointments = Appointment.query.filter_by(status='pending').count()
    
    recent_appointments = []
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    for apt in appointments:
        recent_appointments.append({
            'patient_name': apt.patient.name if apt.patient else 'Unknown',
            'doctor_name': apt.doctor.user.name if apt.doctor and apt.doctor.user else 'Unknown',
            'date': apt.appointment_dt.strftime('%d %b, %H:%M') if apt.appointment_dt else 'N/A',
            'status': apt.status
        })
    
    recent_doctors = []
    doctors = Doctor.query.order_by(Doctor.id.desc()).limit(5).all()
    for doc in doctors:
        recent_doctors.append({
            'name': doc.user.name if doc.user else 'Unknown',
            'specialization': doc.specialization.name if doc.specialization else 'General',
            'joined_date': doc.user.created_at.strftime('%d %b %Y') if doc.user and doc.user.created_at else 'N/A'
        })
    
    return render_template('dashboard.html', 
                         total_users=total_users,
                         total_appointments=total_appointments,
                         total_doctors=total_doctors,
                         pending_appointments=pending_appointments,
                         recent_appointments=recent_appointments,
                         recent_doctors=recent_doctors,
                         new_users_last_30d=0,
                         active_doctors=Doctor.query.filter_by(is_available=True).count(),
                         completion_rate=85)

@app.route('/admin/doctors')
@login_required
def manage_doctors():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    doctors = Doctor.query.all()
    return render_template('doctors.html', doctors=doctors)

@app.route('/admin/doctors/add', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    specializations = Specialization.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        specialization_id = request.form.get('specialization_id')
        qualification = request.form.get('qualification')
        experience = request.form.get('experience')
        fee = request.form.get('fee')
        bio = request.form.get('bio')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('add_doctor'))
        
        hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_pwd,
            role='doctor'
        )
        db.session.add(new_user)
        db.session.commit()
        
        new_doctor = Doctor(
            user_id=new_user.id,
            specialization_id=specialization_id if specialization_id else None,
            qualification=qualification,
            experience_years=int(experience) if experience else 0,
            consultation_fee=float(fee) if fee else 500,
            bio=bio
        )
        db.session.add(new_doctor)
        db.session.commit()
        
        flash(f'Doctor {name} added successfully!', 'success')
        return redirect(url_for('manage_doctors'))
    
    return render_template('add_doctor.html', specializations=specializations)

@app.route('/admin/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    specializations = Specialization.query.all()
    
    if request.method == 'POST':
        try:
            doctor.user.name = request.form.get('name')
            doctor.user.email = request.form.get('email')
            doctor.specialization_id = request.form.get('specialization_id')
            doctor.qualification = request.form.get('qualification')
            doctor.experience_years = int(request.form.get('experience', 0))
            doctor.consultation_fee = float(request.form.get('fee', 500))
            doctor.bio = request.form.get('bio')
            
            db.session.commit()
            flash('Doctor updated successfully!', 'success')
            return redirect(url_for('manage_doctors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating doctor: {str(e)}', 'danger')
            return redirect(url_for('edit_doctor', doctor_id=doctor_id))
    
    return render_template('edit_doctor.html', doctor=doctor, specializations=specializations)

@app.route('/admin/doctors/<int:doctor_id>/delete', methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    user = doctor.user
    
    db.session.delete(doctor)
    db.session.delete(user)
    db.session.commit()
    
    flash('Doctor deleted successfully', 'success')
    return redirect(url_for('manage_doctors'))

@app.route('/admin/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('manage_users'))
    
    if user.role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        if doctor:
            db.session.delete(doctor)
    
    appointments = Appointment.query.filter(
        (Appointment.patient_id == user.id) | (Appointment.doctor_id == user.id)
    ).all()
    for apt in appointments:
        db.session.delete(apt)
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.name} deleted successfully!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/appointments')
@login_required
def admin_appointments():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return render_template('admin_appointments.html', appointments=appointments, now=datetime.now())

@app.route('/admin/appointments/<int:appointment_id>/confirm', methods=['POST'])
@login_required
def confirm_appointment(appointment_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = 'confirmed'
    db.session.commit()
    
    flash(f'Appointment #{appointment_id} confirmed!', 'success')
    return redirect(url_for('admin_appointments'))

@app.route('/admin/appointments/<int:appointment_id>/delete', methods=['POST'])
@login_required
def admin_delete_appointment(appointment_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    
    flash(f'Appointment #{appointment_id} deleted!', 'success')
    return redirect(url_for('admin_appointments'))

# ==================== DOCTOR ROUTES ====================

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.appointment_dt.desc()).all() if doctor else []
    
    return render_template('doctor_dashboard.html', appointments=appointments, doctor=doctor)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)