from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/')
appointments_bp = Blueprint('appointments', __name__, url_prefix='/')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import routes
from app.routes import auth, appointments, admin