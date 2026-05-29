from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Doctor, Appointment

admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_users':        User.query.count(),
        'total_doctors':      Doctor.query.count(),
        'total_appointments': Appointment.query.count(),
        'pending':            Appointment.query.filter_by(status='pending').count(),
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin.route('/doctors')
@login_required
@admin_required
def doctors():
    all_doctors = Doctor.query.all()
    return render_template('admin/doctors.html', doctors=all_doctors)