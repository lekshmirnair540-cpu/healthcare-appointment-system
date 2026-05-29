from app.models import Doctor  # Make sure this import exists

# For the booking page route
@app.route('/appointments/book')
def book_appointment():
    doctors = Doctor.query.all()  # This fetches all doctors
    return render_template('book_appointment.html', doctors=doctors)