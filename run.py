"""
Application entry point.

Creates the Flask application via the factory in :mod:`app` and starts
the development server when executed directly (``python run.py``).
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
