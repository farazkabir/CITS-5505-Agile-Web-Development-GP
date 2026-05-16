"""
Application configuration.

Loads environment variables from a ``.env`` file in the project root and
exposes them through the :class:`Config` class used by the Flask app factory.
"""

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    """Central configuration consumed by ``create_app``.

    Secrets and API keys are read from environment variables so they stay
    out of version control.  Sensible defaults are provided for local
    development.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"timeout": 30},
        "pool_pre_ping": True,
    }

    NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    # Minutes between automatic news-fetch cycles
    NEWS_FETCH_INTERVAL = int(os.environ.get("NEWS_FETCH_INTERVAL", 60))