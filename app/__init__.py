from flask import Flask
from marshmallow.exceptions import ValidationError

from app.config import Config  # Import configuration settings
from app.extensions import db, migrate, bcrypt, jwt, mail, redis_client
from app.urls import register_blueprints
from app.utils.jwt_handlers import register_jwt_error_handlers
from app.celery_app import make_celery
from app.utils.exceptions import handle_error


def create_app():
    """Factory function to create and configure the Flask application"""
    app = Flask(__name__)  # Create Flask app instance
    app.config.from_object(Config)  # Load configuration from config.py

    # Initialize Flask extensions
    db.init_app(app)  # Initialize SQLAlchemy
    migrate.init_app(app, db)  # Initialize Flask-Migrate
    mail.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)  # Initialize JWT authentication

    # Register JWT error handlers
    register_jwt_error_handlers(jwt)

    # Register Blueprints (URLs)
    register_blueprints(app)

    app.celery = make_celery(app)
    handle_error(app)

    return app  # Return the Flask app instance


# importing all the models
from app import models
