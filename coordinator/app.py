from flask import Flask
import os
from .extensions import db, celery
from .routes import main_bp
from .models import TestResult, DNSRecord

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)

    # --- Configuration ---
    # Load configuration from environment variables
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/digdug_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # --- Initialize Extensions ---
    db.init_app(app)

    # Update celery configuration from Flask app config
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )
    # This makes the celery instance app-aware
    celery.conf.update(app.config, force=True)


    # --- Register Blueprints ---
    app.register_blueprint(main_bp)


    # --- Create Database Tables ---
    # Using app_context to ensure the application context is available
    with app.app_context():
        db.create_all()

    return app