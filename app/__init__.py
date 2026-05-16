"""
NewsPulse application package.

Provides the Flask application factory (:func:`create_app`) and initialises
shared extensions (database, migrations, login manager, CSRF protection,
and the background job scheduler).
"""

import os
import logging
import threading

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = BackgroundScheduler(daemon=True)

login_manager.login_view = "main.signin"
login_manager.login_message = "Please sign in to access this page."
login_manager.login_message_category = "warning"

logging.basicConfig(level=logging.INFO)


def seed_bots(app):
    """Ensure default bot personas exist in the database."""
    from app.models import Bot

    DEFAULT_BOTS = [
        {"name": "Satire Sam", "style": "satire", "style_icon": "emoji-laughing", "description": "Turns serious headlines into sharp, satirical takes with dry humor."},
        {"name": "Meme Mike", "style": "meme", "style_icon": "lightning-charge-fill", "description": "Finds the internet angle in every story and rewrites it with meme energy."},
        {"name": "Breaking Blake", "style": "breaking", "style_icon": "megaphone", "description": "Delivers fast, urgent updates on developing stories and major news moments."},
        {"name": "GoodVibes Grace", "style": "wholesome", "style_icon": "heart", "description": "Highlights uplifting stories, community wins, and news with a positive spin."},
        {"name": "Curious Quinn", "style": "question", "style_icon": "question-circle", "description": "Frames news as thoughtful questions that invite reflection and discussion."},
        {"name": "RantRadar Rex", "style": "anger", "style_icon": "fire", "description": "Tracks frustrating headlines and responds with bold, opinionated hot takes."},
    ]

    with app.app_context():
        for bot_data in DEFAULT_BOTS:
            existing = Bot.query.filter_by(style=bot_data["style"]).first()
            if existing:
                existing.name = bot_data["name"]
                existing.style_icon = bot_data["style_icon"]
                existing.description = bot_data["description"]
            else:
                db.session.add(Bot(**bot_data))
        db.session.commit()


def start_news_scheduler(app):
    """Start the background news-fetch scheduler and fire an initial cycle.

    Must be called exactly once in the actual worker process (not the
    Werkzeug reloader parent).
    """
    from app.news_service import run_news_cycle

    interval = app.config.get("NEWS_FETCH_INTERVAL", 60)
    scheduler.add_job(
        run_news_cycle,
        "interval",
        minutes=interval,
        args=[app],
        id="news_cycle",
        replace_existing=True,
        max_instances=1,
    )
    if not scheduler.running:
        scheduler.start()

    def _startup_fetch():
        import time
        time.sleep(8)
        run_news_cycle(app)

    t = threading.Thread(target=_startup_fetch, daemon=True)
    t.start()


def create_app(config_class=None):
    """Create and configure the Flask application.

    Initialises extensions, registers blueprints, seeds the database with
    default bot personas, and starts the background news-fetch scheduler.

    Args:
        config_class: Optional configuration class. Defaults to :class:`Config`.

    Returns:
        Flask: The fully configured application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class or Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models
    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()
        seed_bots(app)

    return app