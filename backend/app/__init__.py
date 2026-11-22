import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from .extensions import db

load_dotenv()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
jwt = JWTManager()


def _migrate_telemetry_switch_level():
    """Add switch_level to databases created by an earlier FloodGuard version."""
    columns = {column["name"] for column in inspect(db.engine).get_columns("telemetry")}
    if "switch_level" not in columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE telemetry ADD COLUMN switch_level INTEGER"))


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "dev-only-change-me-too"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///floodguard.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=1024 * 1024,
        JSON_SORT_KEYS=False,
    )
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    CORS(app, resources={r"/api/*": {"origins": [origin.strip() for origin in origins]}})
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins=origins)

    from .models import User, Sensor, Telemetry, Alert, SafeLocation, Notification
    from . import socket_events  # register authenticated Socket.IO connection handler
    from .api.auth import bp as auth_bp
    from .api.telemetry import bp as telemetry_bp
    from .api.admin import bp as admin_bp
    from .api.member import bp as member_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(telemetry_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(member_bp, url_prefix="/api/v1")

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "service": "floodguard-api"}

    with app.app_context():
        db.create_all()
        _migrate_telemetry_switch_level()

    return app
