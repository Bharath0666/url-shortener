"""
URL Shortener — Flask Application Factory
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from app.config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_class)

    # ---- Extensions ----
    db.init_app(app)
    CORS(app)

    # ---- Rate Limiter ----
    from app.rate_limiter import limiter
    limiter.init_app(app)

    # ---- Blueprints / Routes ----
    from app.routes import api_bp, redirect_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(redirect_bp)

    # ---- Create tables if they don't exist ----
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
