from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import db, bcrypt
from app.models import User
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def generate_slug(name):
    slug = re.sub(r'\s+', '', name).lower()
    base = slug
    i = 1
    while User.query.filter_by(slug=slug).first():
        slug = f"{base}{i}"
        i += 1
    return slug

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    slug = generate_slug(data['name'])
    user = User(name=data['name'], email=data['email'], password_hash=hashed, slug=slug)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': {'id': user.id, 'name': user.name, 'slug': user.slug}}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': {'id': user.id, 'name': user.name, 'slug': user.slug}}), 200