from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Waitlist

waitlist_bp = Blueprint('waitlist', __name__, url_prefix='/waitlist')

@waitlist_bp.route('', methods=['GET'])
@jwt_required()
def get_waitlist():
    user_id = int(get_jwt_identity())
    entries = Waitlist.query.filter_by(host_user_id=user_id).all()
    return jsonify([{
        'id': e.id,
        'guest_name': e.guest_name,
        'guest_email': e.guest_email,
        'guest_reason': e.guest_reason,
        'preferred_start': e.preferred_start.isoformat(),
        'preferred_end': e.preferred_end.isoformat(),
        'status': e.status,
        'created_at': e.created_at.isoformat()
    } for e in entries]), 200

@waitlist_bp.route('/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def remove_from_waitlist(entry_id):
    entry = Waitlist.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Removed'}), 200