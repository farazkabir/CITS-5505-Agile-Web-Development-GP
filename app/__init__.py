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
        {"name": "SatireDesk", "style": "satire", "style_icon": "emoji-laughing", "description": "Skewering tech culture and corporate speak with dry wit."},
        {"name": "MemeKing", "style": "meme", "style_icon": "lightning-charge-fill", "description": "Relatable formats, chaotic energy, zero chill."},
        {"name": "BreakingDesk", "style": "breaking", "style_icon": "megaphone", "description": "Urgent breaking-news style posts on tech & world events."},
        {"name": "WholesomeBot", "style": "wholesome", "style_icon": "heart", "description": "Good news, community wins, and feel-good stories."},
        {"name": "QuickQuestion", "style": "question", "style_icon": "question-circle", "description": "Thought-provoking open questions that invite discussion."},
        {"name": "RageBot", "style": "anger", "style_icon": "fire", "description": "Hot takes and strong opinions on outrageous news."},
    ]

    with app.app_context():
        for bot_data in DEFAULT_BOTS:
            existing = Bot.query.filter_by(name=bot_data["name"]).first()
            if not existing:
                db.session.add(Bot(**bot_data))
        db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models
    from app.routes import main
    app.register_blueprint(main)

    # In debug mode, only the reloader child (WERKZEUG_RUN_MAIN) should touch the DB
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        with app.app_context():
            db.create_all()
            seed_bots(app)

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

        # One-shot startup fetch via a thread (avoids APScheduler overlap)
        def _startup_fetch():
            import time
            time.sleep(8)
            run_news_cycle(app)

        t = threading.Thread(target=_startup_fetch, daemon=True)
        t.start()

    return app