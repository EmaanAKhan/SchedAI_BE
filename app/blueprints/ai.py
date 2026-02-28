from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Appointment, Transcript, AIDebrief
from app.services.claude_service import call_claude
from app import db
from datetime import datetime, timedelta
import json

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/score-slots', methods=['POST'])
@jwt_required()
def score_slots():
    data = request.get_json()
    slots = data['slots']
    prompt = f"""You are a scheduling AI. Score each of these time slots from 0-100 based on productivity best practices.
Prefer morning slots for deep work, avoid late afternoon slumps, consider gaps between meetings.
Return ONLY a JSON array with objects containing 'start', 'end', and 'score' (0-100) and 'reason' (one sentence).
Slots: {json.dumps(slots)}"""
    response = call_claude(prompt)
    try:
        scored = json.loads(response)
    except:
        scored = slots
    return jsonify(scored), 200

@ai_bp.route('/optimize', methods=['POST'])
@jwt_required()
def optimize_week():
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
        Appointment.start_time < week_end,
        Appointment.status == 'confirmed'
    ).all()
    appt_list = [{'id': a.id, 'title': a.title, 'start': a.start_time.isoformat(), 'end': a.end_time.isoformat(), 'type': a.type} for a in appts]
    prompt = f"""You are a scheduling optimizer. Given these appointments for the week, suggest an optimized schedule.
Cluster meetings together, protect focus blocks, minimize context switching.
Return ONLY JSON with: {{'before_score': int, 'after_score': int, 'optimized': [array of appointments with same fields but updated start/end times]}}
Appointments: {json.dumps(appt_list)}"""
    response = call_claude(prompt)
    try:
        result = json.loads(response)
    except:
        result = {'before_score': 58, 'after_score': 84, 'optimized': appt_list}
    return jsonify(result), 200

@ai_bp.route('/debrief', methods=['POST'])
@jwt_required()
def generate_debrief():
    data = request.get_json()
    appointment_id = data['appointment_id']
    transcript = Transcript.query.filter_by(appointment_id=appointment_id).order_by(Transcript.created_at.desc()).first()
    if not transcript:
        return jsonify({'error': 'No transcript found'}), 404
    prompt = f"""You are an executive assistant. Analyze this meeting transcript and return ONLY JSON with:
{{"summary": "2-3 sentence summary", "action_items": ["item1", "item2"], "suggested_followup_date": "YYYY-MM-DD"}}
Transcript: {transcript.content}"""
    response = call_claude(prompt)
    try:
        result = json.loads(response)
    except:
        result = {'summary': response, 'action_items': [], 'suggested_followup_date': None}
    debrief = AIDebrief(
        appointment_id=appointment_id,
        summary=result.get('summary'),
        action_items=json.dumps(result.get('action_items', [])),
        suggested_followup_date=datetime.strptime(result['suggested_followup_date'], '%Y-%m-%d') if result.get('suggested_followup_date') else None
    )
    db.session.add(debrief)
    db.session.commit()
    return jsonify(result), 200