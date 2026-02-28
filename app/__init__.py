from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    CORS(app)

    from app.blueprints.auth import auth_bp
    from app.blueprints.workspaces import workspaces_bp
    from app.blueprints.availability import availability_bp
    from app.blueprints.appointments import appointments_bp
    from app.blueprints.public import public_bp
    from app.blueprints.ai import ai_bp
    from app.blueprints.n8n import n8n_bp
    from app.blueprints.waitlist import waitlist_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(workspaces_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(n8n_bp)
    app.register_blueprint(waitlist_bp)

    return app