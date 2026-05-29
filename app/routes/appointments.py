from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Doctor, Appointment
from app.routes import appointments_bp
from datetime import datetime

@appointments_bp.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason')
        
        if not doctor_id or not appointment_date or not appointment_time:
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('appointments.book_appointment'))
        
        # Combine date and time into a single datetime
        appointment_datetime_str = f"{appointment_date} {appointment_time}"
        appointment_dt = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %H:%M')
        
        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            appointment_dt=appointment_dt,
            reason=reason,
            status='pending'
        )
        
        try:
            db.session.add(appointment)
            db.session.commit()
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('appointments.view_appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error booking appointment: {str(e)}', 'danger')
            return redirect(url_for('appointments.book_appointment'))
    
    # GET request - Fetch all doctors
    doctors = Doctor.query.all()
    return render_template('appointments/book.html', doctors=doctors)

@appointments_bp.route('/appointments')
@login_required
def view_appointments():
    all_appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.appointment_dt.desc()).all()
    return render_template('appointments/list.html', appointments=all_appointments)

@appointments_bp.route('/appointments/cancel/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != current_user.id:
        flash('You are not authorized to cancel this appointment', 'danger')
        return redirect(url_for('appointments.view_appointments'))
    
    appointment.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled successfully', 'success')
    return redirect(url_for('appointments.view_appointments'))