from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

from app.models.base import Base

# Pass the custom Base to Flask-SQLAlchemy so models are registered
db = SQLAlchemy(model_class=Base)

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'yoga_sutras.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

    # Register blueprints
    from app.routes.text_routes import text_bp
    from app.routes.dictionary_routes import dict_bp

    app.register_blueprint(text_bp)
    app.register_blueprint(dict_bp)

    with app.app_context():
        db.create_all()

    return app
