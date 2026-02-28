from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Appointment, Waitlist
from app.services.slot_generator import generate_slots
from datetime import datetime, timedelta, date

public_bp = Blueprint('public', __name__, url_prefix='/public')

@public_bp.route('/slots/<slug>', methods=['GET'])
def get_public_slots(slug):
    user = User.query.filter_by(slug=slug).first_or_404()
    slots = []
    today = date.today()
    for i in range(7):
        target = today + timedelta(days=i)
        day_slots = generate_slots(user.id, target)
        slots.extend(day_slots)
    return jsonify({'user': {'name': user.name, 'slug': user.slug}, 'slots': slots}), 200

@public_bp.route('/book/<slug>', methods=['POST'])
def book_slot(slug):
    user = User.query.filter_by(slug=slug).first_or_404()
    data = request.get_json()
    start = datetime.fromisoformat(data['start_time'])
    end = datetime.fromisoformat(data['end_time'])

    # check if slot is still free
    conflict = Appointment.query.filter(
        Appointment.host_user_id == user.id,
        Appointment.status == 'confirmed',
        Appointment.start_time < end,
        Appointment.end_time > start
    ).first()

    if conflict:
        # return 3 next available slots instead of error
        next_slots = generate_slots(user.id, start.date())
        available = [s for s in next_slots if s['start'] > data['start_time']][:3]
        return jsonify({'available': False, 'next_slots': available}), 409

    appt = Appointment(
        host_user_id=user.id,
        guest_name=data['guest_name'],
        guest_email=data['guest_email'],
        title=data.get('title', f"Meeting with {data['guest_name']}"),
        reason=data.get('reason'),
        start_time=start,
        end_time=end,
        type='external'
    )
    db.session.add(appt)
    db.session.commit()
    return jsonify({'message': 'Booked', 'appointment_id': appt.id}), 201

@public_bp.route('/waitlist/<slug>', methods=['POST'])
def join_waitlist(slug):
    user = User.query.filter_by(slug=slug).first_or_404()
    data = request.get_json()
    entry = Waitlist(
        host_user_id=user.id,
        guest_name=data['guest_name'],
        guest_email=data['guest_email'],
        guest_reason=data.get('reason'),
        preferred_start=datetime.fromisoformat(data['preferred_start']),
        preferred_end=datetime.fromisoformat(data['preferred_end'])
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'message': 'Added to waitlist'}), 201