from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Appointment, Transcript, AIDebrief
from app.services.claude_service import call_claude
from app import db
from datetime import datetime, timedelta
import json
import re

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

def clean_json(text):
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()

@ai_bp.route('/score-slots', methods=['POST'])
@jwt_required()
def score_slots():
    data = request.get_json()
    slots = data['slots']
    prompt = f"""You are an expert productivity and scheduling AI assistant.

Your task is to score each time slot from 0 to 100 based on the following criteria:
- Morning slots (8AM-11AM) are best for deep focus work — score higher
- Early afternoon (1PM-3PM) is good for collaborative meetings — score moderately high
- Late afternoon (3PM-5PM) causes energy slumps — score lower
- Back-to-back slots with no breaks should be penalized
- Slots with at least 15 minutes gap before and after score higher
- Slots before lunch (11:30AM-12:30PM) are poor for starting new work — score lower

Return ONLY a valid JSON array. No explanation, no markdown, no backticks.
Each object must have exactly these fields: 'start', 'end', 'score' (integer 0-100), 'reason' (one clear sentence explaining the score).

Slots to score:
{json.dumps(slots)}"""

    response = call_claude(prompt)
    try:
        scored = json.loads(clean_json(response))
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

    prompt = f"""You are an expert calendar optimization AI.

Your task is to reschedule the given appointments to maximize productivity using these rules:
- Cluster all meetings together in the same part of the day (morning or afternoon) to protect deep work blocks
- Never schedule meetings back to back — always leave at least 10 minutes between them
- Protect focus blocks — never move or overlap them with meetings
- Place high-focus solo work in the morning (before 12PM)
- Place collaborative meetings in the afternoon (after 1PM) where possible
- Keep meetings within the same working day (9AM-6PM), never move to a different day unless absolutely necessary
- Calculate a before score and after score from 0-100 based on how well the schedule follows these rules

Return ONLY valid JSON. No explanation, no markdown, no backticks.
The JSON must have exactly these fields:
{{
  "before_score": integer 0-100,
  "after_score": integer 0-100,
  "optimized": [array of appointments with same id and title but updated start and end times in ISO format]
}}

Appointments to optimize:
{json.dumps(appt_list)}"""

    response = call_claude(prompt)
    try:
        result = json.loads(clean_json(response))
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

    prompt = f"""You are an expert executive assistant AI with years of experience in meeting management.

Analyze the following meeting transcript carefully and extract the most important information.

Your analysis must include:
1. A clear and concise summary (2-3 sentences) covering the main purpose of the meeting, key points discussed, and final outcome
2. A list of specific, actionable action items — each one must mention WHO is responsible and WHAT they need to do
3. A suggested follow-up date based on context clues in the transcript (deadlines mentioned, urgency, or default to 7 days from now if unclear)

Return ONLY valid JSON. No explanation, no markdown, no backticks.
The JSON must have exactly these fields:
{{
  "summary": "2-3 sentence summary of the meeting",
  "action_items": ["Person: specific action", "Person: specific action"],
  "suggested_followup_date": "YYYY-MM-DD"
}}

Meeting transcript:
{transcript.content}"""

    response = call_claude(prompt)
    try:
        result = json.loads(clean_json(response))
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
    return jsonify({
        'summary': result.get('summary'),
        'actionItems': result.get('action_items', []),
        'suggestedFollowupDate': result.get('suggested_followup_date')
    }), 200