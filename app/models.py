import hashlib
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Original name entered during sign up
    name = db.Column(db.String(80), nullable=False)

    # Public display name shown on profile/comments
    display_name = db.Column(db.String(80), nullable=True)

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Public profile fields
    bio = db.Column(db.String(160), default="")
    website = db.Column(db.String(255), default="")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    style = db.Column(db.String(32), nullable=False)
    style_icon = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), default="")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    posts = db.relationship("Post", backref="bot", lazy="dynamic")


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey("bot.id"), nullable=False)

    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(512), default="")
    source_title = db.Column(db.String(300), default="")

    # SHA-256 of source_url to prevent duplicate posts from the same article
    source_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    votes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def make_hash(url: str, bot_name: str) -> str:
        """Unique hash per (article_url, bot) pair to avoid duplicate posts."""
        raw = f"{url}|{bot_name}"
        return hashlib.sha256(raw.encode()).hexdigest()

class Vote(db.Model):
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
