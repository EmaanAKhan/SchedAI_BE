from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Workspace(db.Model):
    __tablename__ = 'workspaces'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    invite_code = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WorkspaceMember(db.Model):
    __tablename__ = 'workspace_members'
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(20), default='member')

class AvailabilityRule(db.Model):
    __tablename__ = 'availability_rules'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    day_of_week = db.Column(db.Integer)  # 0=Mon, 6=Sun
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    buffer_minutes = db.Column(db.Integer, default=0)
    is_bookable = db.Column(db.Boolean, default=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=True)
    host_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    guest_name = db.Column(db.String(100), nullable=True)
    guest_email = db.Column(db.String(150), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(20), default='meeting')  # meeting | focus | external
    status = db.Column(db.String(20), default='confirmed')  # confirmed | cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transcript(db.Model):
    __tablename__ = 'transcripts'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AIDebrief(db.Model):
    __tablename__ = 'ai_debriefs'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    summary = db.Column(db.Text)
    action_items = db.Column(db.Text)
    suggested_followup_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Waitlist(db.Model):
    __tablename__ = 'waitlist'
    id = db.Column(db.Integer, primary_key=True)
    host_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    guest_name = db.Column(db.String(100), nullable=False)
    guest_email = db.Column(db.String(150), nullable=False)
    guest_reason = db.Column(db.Text, nullable=True)
    preferred_start = db.Column(db.DateTime, nullable=False)
    preferred_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='waiting')  # waiting | booked | expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)