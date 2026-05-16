"""
SQLAlchemy models for NewsPulse.

Defines the core domain entities: :class:`User`, :class:`Bot`, :class:`Post`,
:class:`Vote`, and :class:`Comment`.  Also registers the Flask-Login user
loader callback.
"""

import hashlib
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    """Registered platform user with authentication and profile data."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    display_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    bio = db.Column(db.String(160), default="")
    website = db.Column(db.String(255), default="")
    profile_pic = db.Column(db.String(255), default="")

    @property
    def public_name(self):
        """Return display_name if set, otherwise fall back to name."""
        return self.display_name or self.name

    def set_password(self, password):
        """Hash and store the given plaintext password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify *password* against the stored hash."""
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login callback to reload a user from the session-stored ID."""
    return db.session.get(User, int(user_id))


class Bot(db.Model):
    """AI persona that generates styled news posts."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    style = db.Column(db.String(32), nullable=False)
    style_icon = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), default="")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    posts = db.relationship("Post", backref="bot", lazy="dynamic")


class Post(db.Model):
    """AI-generated news post belonging to a :class:`Bot`."""

    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey("bot.id"), nullable=False)

    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(512), default="")
    source_title = db.Column(db.String(300), default="")

    # SHA-256 of (source_url + bot_name) — prevents duplicate posts
    source_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    votes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def make_hash(url: str, bot_name: str) -> str:
        """Return a deterministic SHA-256 hex digest for a (URL, bot) pair."""
        raw = f"{url}|{bot_name}"
        return hashlib.sha256(raw.encode()).hexdigest()


class Vote(db.Model):
    """Records a single user's up- or down-vote on a post.

    The ``unique_user_post_vote`` constraint ensures one vote per user per
    post at the database level.
    """

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # 1 = upvote, -1 = downvote
    value = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    post = db.relationship("Post", backref=db.backref("vote_records", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("votes", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("post_id", "user_id", name="unique_user_post_vote"),
    )


class Comment(db.Model):
    """User-authored comment attached to a :class:`Post`."""

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    post = db.relationship("Post", backref=db.backref("comments", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("comments", lazy="dynamic"))

class Vote(db.Model):
    """Tracks which user upvoted which post (one vote per user per post)."""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("post_id", "user_id", name="uq_vote_post_user"),)

    post = db.relationship("Post", backref=db.backref("votes_list", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("votes", lazy="dynamic"))
