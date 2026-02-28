from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Appointment, Transcript
from app.services.conflict_checker import check_conflicts
from app.services.waitlist_checker import check_waitlist
from datetime import datetime, timedelta

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointments_bp.route('', methods=['GET'])
@jwt_required()
def get_appointments():
    user_id = int(get_jwt_identity())
    week_str = request.args.get('week')
    if week_str:
        week_start = datetime.strptime(week_str, '%Y-%m-%d')
    else:
        today = datetime.utcnow()
        week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    appts = Appointment.query.filter(
        Appointment.host_user_id == user_id,
        Appointment.start_time >= week_start,
        Appointment.start_time < week_end
    ).all()
    return jsonify([serialize(a) for a in appts]), 200

@appointments_bp.route('', methods=['POST'])
@jwt_required()
def create_appointment():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    start = datetime.fromisoformat(data['start_time'])
    end = datetime.fromisoformat(data['end_time'])
    conflict = check_conflicts(user_id, start, end)
    if conflict['conflict']:
        return jsonify(conflict), 409
    appt = Appointment(
        host_user_id=user_id,
        workspace_id=data.get('workspace_id'),
        guest_name=data.get('guest_name'),
        guest_email=data.get('guest_email'),
        title=data['title'],
        reason=data.get('reason'),
        start_time=start,
        end_time=end,
        type=data.get('type', 'meeting')
    )
    db.session.add(appt)
    db.session.commit()
    return jsonify(serialize(appt)), 201

@appointments_bp.route('/<int:appt_id>', methods=['PATCH'])
@jwt_required()
def update_appointment(appt_id):
    user_id = int(get_jwt_identity())
    appt = Appointment.query.get_or_404(appt_id)
    data = request.get_json()
    if 'start_time' in data and 'end_time' in data:
        start = datetime.fromisoformat(data['start_time'])
        end = datetime.fromisoformat(data['end_time'])
        conflict = check_conflicts(user_id, start, end, exclude_id=appt_id)
        if conflict['conflict']:
            return jsonify(conflict), 409
        appt.start_time = start
        appt.end_time = end
        db.session.commit()
        check_waitlist(user_id)
    if 'title' in data:
        appt.title = data['title']
    if 'status' in data:
        appt.status = data['status']
    db.session.commit()
    return jsonify(serialize(appt)), 200

@appointments_bp.route('/<int:appt_id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(appt_id):
    user_id = int(get_jwt_identity())
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'cancelled'
    db.session.commit()
    booked = check_waitlist(user_id)
    return jsonify({'message': 'Cancelled', 'waitlist_booked': booked}), 200

@appointments_bp.route('/<int:appt_id>/transcript', methods=['POST'])
@jwt_required()
def save_transcript(appt_id):
    data = request.get_json()
    transcript = Transcript(appointment_id=appt_id, content=data['content'])
    db.session.add(transcript)
    db.session.commit()
    return jsonify({'message': 'Transcript saved', 'id': transcript.id}), 201

@appointments_bp.route('/<int:appt_id>/ics', methods=['GET'])
def get_ics(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:{appt.title}
DTSTART:{appt.start_time.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{appt.end_time.strftime('%Y%m%dT%H%M%SZ')}
DESCRIPTION:{appt.reason or ''}
END:VEVENT
END:VCALENDAR"""
    return Response(ics, mimetype='text/calendar',
                    headers={'Content-Disposition': f'attachment; filename=appointment_{appt_id}.ics'})

def serialize(a):
    return {
        'id': a.id,
        'title': a.title,
        'guest_name': a.guest_name,
        'guest_email': a.guest_email,
        'start_time': a.start_time.isoformat(),
        'end_time': a.end_time.isoformat(),
        'type': a.type,
        'status': a.status,
        'reason': a.reason
    }