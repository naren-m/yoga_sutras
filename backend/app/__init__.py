from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

from app.models.base import Base

# Pass the custom Base to Flask-SQLAlchemy so models are registered
db = SQLAlchemy(model_class=Base)

# Data directory - use env var in Docker, or calculate from file path for local dev
# In Docker: /app/data (mounted volume)
# Locally: ../../data relative to backend/app/__init__.py
DATA_DIR = os.environ.get('DATA_DIR', os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data'
))

def create_app():
    app = Flask(__name__)

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(DATA_DIR, 'yoga_sutras.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=[
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:3002',   # Docker frontend port
        'http://127.0.0.1:3002',
        'http://localhost:5173',   # Vite default port
    ])

    # Register blueprints
    from app.routes.text_routes import text_bp
    from app.routes.dictionary_routes import dict_bp

    app.register_blueprint(text_bp)
    app.register_blueprint(dict_bp)

    with app.app_context():
        db.create_all()

    # Observability via shared homelab-observability lib. No-op if the lib
    # isn't installed (e.g. minimal dev shells). Reads HOMELAB_* env vars
    # injected by the homelab-observability Kustomize component at deploy time.
    _setup_observability(app)

    return app


def _setup_observability(app):
    """Wire OpenTelemetry tracing + metrics + Loki logging via homelab-observability."""
    try:
        import homelab_observability as hobs
    except ImportError:
        return
    hobs.setup(service_name="yoga-sutras-backend", flask_app=app)
