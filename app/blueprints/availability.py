from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import AvailabilityRule, User
from app.services.slot_generator import generate_slots
from datetime import datetime

availability_bp = Blueprint('availability', __name__, url_prefix='/availability')

@availability_bp.route('', methods=['POST'])
@jwt_required()
def save_availability():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    # delete existing rules and replace
    AvailabilityRule.query.filter_by(user_id=user_id).delete()
    for rule in data['rules']:
        r = AvailabilityRule(
            user_id=user_id,
            day_of_week=rule['day_of_week'],
            start_time=datetime.strptime(rule['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(rule['end_time'], '%H:%M').time(),
            buffer_minutes=rule.get('buffer_minutes', 0),
            is_bookable=rule.get('is_bookable', True)
        )
        db.session.add(r)
    db.session.commit()
    return jsonify({'message': 'Availability saved'}), 200

@availability_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_availability(user_id):
    rules = AvailabilityRule.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'day_of_week': r.day_of_week,
        'start_time': r.start_time.strftime('%H:%M'),
        'end_time': r.end_time.strftime('%H:%M'),
        'buffer_minutes': r.buffer_minutes,
        'is_bookable': r.is_bookable
    } for r in rules]), 200

@availability_bp.route('/<int:user_id>/slots', methods=['GET'])
def get_slots(user_id):
    date_str = request.args.get('date')
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    slots = generate_slots(user_id, target_date)
    return jsonify(slots), 200