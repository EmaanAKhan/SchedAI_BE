from flask import Blueprint, jsonify
from app.models import Appointment
from datetime import datetime, timedelta, date

n8n_bp = Blueprint('n8n', __name__, url_prefix='/n8n')

@n8n_bp.route('/tomorrow-appointments', methods=['GET'])
def tomorrow_appointments():
    tomorrow = date.today() + timedelta(days=1)
    start = datetime.combine(tomorrow, datetime.min.time())
    end = start + timedelta(days=1)
    appts = Appointment.query.filter(
        Appointment.start_time >= start,
        Appointment.start_time < end,
        Appointment.status == 'confirmed',
        Appointment.guest_email != None
    ).all()
    return jsonify([{
        'appointment_id': a.id,
        'title': a.title,
        'guest_name': a.guest_name,
        'guest_email': a.guest_email,
        'start_time': a.start_time.isoformat(),
        'end_time': a.end_time.isoformat()
    } for a in appts]), 200