from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Workspace, WorkspaceMember, User, Appointment
from datetime import date, datetime, timedelta
import random, string

workspaces_bp = Blueprint('workspaces', __name__, url_prefix='/workspaces')

def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@workspaces_bp.route('', methods=['POST'])
@jwt_required()
def create_workspace():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    ws = Workspace(name=data['name'], created_by=user_id, invite_code=generate_invite_code())
    db.session.add(ws)
    db.session.flush()
    member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role='owner')
    db.session.add(member)
    db.session.commit()
    return jsonify({'id': ws.id, 'name': ws.name, 'invite_code': ws.invite_code}), 201

@workspaces_bp.route('/join', methods=['POST'])
@jwt_required()
def join_workspace():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    ws = Workspace.query.filter_by(invite_code=data['invite_code']).first()
    if not ws:
        return jsonify({'error': 'Invalid invite code'}), 404
    already = WorkspaceMember.query.filter_by(workspace_id=ws.id, user_id=user_id).first()
    if already:
        return jsonify({'error': 'Already a member'}), 409
    member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role='member')
    db.session.add(member)
    db.session.commit()
    return jsonify({'id': ws.id, 'name': ws.name}), 200

@workspaces_bp.route('/<int:ws_id>/members', methods=['GET'])
@jwt_required()
def get_members(ws_id):
    members = WorkspaceMember.query.filter_by(workspace_id=ws_id).all()
    result = []
    for m in members:
        user = User.query.get(m.user_id)
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = today_start + timedelta(days=1)
        appts = Appointment.query.filter(
            Appointment.host_user_id == user.id,
            Appointment.start_time >= today_start,
            Appointment.start_time < today_end,
            Appointment.status == 'confirmed'
        ).all()
        result.append({
            'user_id': user.id,
            'name': user.name,
            'slug': user.slug,
            'role': m.role,
            'appointments_today': [{'start': a.start_time.isoformat(), 'end': a.end_time.isoformat()} for a in appts]
        })
    return jsonify(result), 200

@workspaces_bp.route('/seed-calendar', methods=['POST'])
@jwt_required()
def seed_calendar():
    user_id = int(get_jwt_identity())
    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    fake = [
        {'title': 'Team Standup', 'guest': 'Team', 'offset_days': 0, 'hour': 9, 'type': 'meeting'},
        {'title': 'Product Review', 'guest': 'Sarah Chen', 'offset_days': 0, 'hour': 11, 'type': 'meeting'},
        {'title': 'Client Call', 'guest': 'John Davis', 'offset_days': 1, 'hour': 14, 'type': 'meeting'},
        {'title': 'Focus Block', 'guest': None, 'offset_days': 1, 'hour': 10, 'type': 'focus'},
        {'title': '1:1 with Manager', 'guest': 'Ali Raza', 'offset_days': 2, 'hour': 15, 'type': 'meeting'},
    ]
    for f in fake:
        start = base + timedelta(days=f['offset_days'])
        start = start.replace(hour=f['hour'])
        end = start + timedelta(minutes=30)
        appt = Appointment(
            host_user_id=user_id,
            title=f['title'],
            guest_name=f.get('guest'),
            start_time=start,
            end_time=end,
            type=f.get('type', 'meeting'),
            status='confirmed'
        )
        db.session.add(appt)
    db.session.commit()
    return jsonify({'message': 'Calendar seeded'}), 200