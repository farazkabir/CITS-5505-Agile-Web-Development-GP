"""
Application entry point.

Creates the Flask application via the factory in :mod:`app` and starts
the development server when executed directly (``python run.py``).
"""

import os

from app import create_app, start_news_scheduler

app = create_app()

if __name__ == "__main__":
    # Werkzeug's reloader spawns a child process with WERKZEUG_RUN_MAIN=true.
    # Only start the background scheduler in that child so news fetching
    # happens exactly once — not in both parent and child.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_news_scheduler(app)

    app.run(debug=True)
