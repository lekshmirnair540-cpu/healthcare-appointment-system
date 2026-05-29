from app import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(20), default='patient')  # patient | doctor | admin
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    appointments  = db.relationship('Appointment', foreign_keys='Appointment.patient_id', backref='patient', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Specialization(db.Model):
    __tablename__ = 'specializations'
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(100), unique=True, nullable=False)
    doctors = db.relationship('Doctor', backref='specialization', lazy=True)


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization_id  = db.Column(db.Integer, db.ForeignKey('specializations.id'))
    bio                = db.Column(db.Text)
    user               = db.relationship('User', backref='doctor_profile')
    appointments       = db.relationship('Appointment', backref='doctor', lazy=True)


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id             = db.Column(db.Integer, primary_key=True)
    patient_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id      = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_dt = db.Column(db.DateTime, nullable=False)
    reason         = db.Column(db.String(300))
    status         = db.Column(db.String(20), default='pending')  # pending | confirmed | cancelled
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)