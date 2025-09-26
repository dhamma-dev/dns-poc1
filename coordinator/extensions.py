from flask_sqlalchemy import SQLAlchemy
from celery import Celery

db = SQLAlchemy()
# The celery instance is created without the app object initially.
# It will be configured and linked to the app inside the app factory.
celery = Celery(__name__, broker='redis://redis:6379/0', backend='redis://redis:6379/0')