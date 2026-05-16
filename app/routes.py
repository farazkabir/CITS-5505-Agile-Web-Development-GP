"""
View routes for the NewsPulse application.

All routes are registered on the ``main`` blueprint and cover the public
feed, authentication, account management, voting, commenting, bot
management, and user profiles.
"""

import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import User, Bot, Post, Comment, Vote
from app.forms import SignUpForm, SignInForm, ProfileForm

ALLOWED_PIC_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

main = Blueprint("main", __name__)


def _time_ago(dt):
    """Return a human-readable relative time string."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    return dt.strftime("%b %d, %Y")


def _get_user_vote(post_id, user_id):
    """Return 'up', 'down', or None for the given user's vote on a post."""
    vote = Vote.query.filter_by(post_id=post_id, user_id=user_id).first()
    if vote is None:
        return None
    return "up" if vote.value == 1 else "down"


def _post_to_dict(post):
    """Convert a :class:`Post` instance to a template-friendly dictionary.

    Includes the current user's vote state so the template can highlight
    the active vote button.
    """
    bot = post.bot

    user_voted = None
    if current_user.is_authenticated:
        user_voted = _get_user_vote(post.id, current_user.id)

    return {
        "id": post.id,
        "author": bot.name,
        "author_description": bot.description,
        "is_bot": True,
        "style": bot.style,
        "style_icon": bot.style_icon,
        "votes": post.votes,
        "user_voted": user_voted,
        "comments": post.comments_count,
        "time_ago": _time_ago(post.created_at),
        "title": post.title,
        "excerpt": post.content,
        "source_url": post.source_url,
    }


POSTS_PER_PAGE = 10


def _build_feed_query(active_filter):
    """Build the base SQLAlchemy query for the news feed.

    Args:
        active_filter: Style key (e.g. ``"satire"``, ``"trending"``) or
            ``"all"`` to show every post.

    Returns:
        A SQLAlchemy query ordered and filtered for the requested view.
    """
    if current_user.is_authenticated:
        query = Post.query.join(Bot).filter(Bot.active == True)
    else:
        query = Post.query.join(Bot)

    if active_filter == "trending":
        total_reactions = db.func.sum(db.func.abs(Vote.value)).label("reaction_count")
        query = (
            query
            .join(Vote, Vote.post_id == Post.id)
            .group_by(Post.id)
            .order_by(total_reactions.desc(), Post.created_at.desc())
        )
    elif active_filter and active_filter != "all":
        query = query.filter(Bot.style == active_filter).order_by(Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())

    return query


@main.route("/")
def index():
    """Render the main news feed with optional style filtering."""
    active_filter = request.args.get("filter", "all")

    if current_user.is_authenticated:
        active_styles = {b.style for b in Bot.query.filter_by(active=True).all()}
    else:
        active_styles = {b.style for b in Bot.query.all()}

    query = _build_feed_query(active_filter)
    posts = [_post_to_dict(p) for p in query.limit(POSTS_PER_PAGE).all()]
    return render_template("index.html", posts=posts, active_filter=active_filter, active_styles=active_styles)


@main.route("/api/posts")
def api_posts():
    """JSON endpoint used by the infinite-scroll front-end to load more posts."""
    active_filter = request.args.get("filter", "all")
    page = request.args.get("page", 1, type=int)

    query = _build_feed_query(active_filter)
    paginated = query.offset((page - 1) * POSTS_PER_PAGE).limit(POSTS_PER_PAGE).all()
    posts = [_post_to_dict(p) for p in paginated]

    return jsonify({"posts": posts, "has_more": len(posts) == POSTS_PER_PAGE})


@main.route("/post/<int:post_id>")
def post_detail(post_id):
    """Display a single post with its full content and comment thread."""
    post = Post.query.get_or_404(post_id)
    comments_list = []
    for c in post.comments.order_by(Comment.created_at.desc()).all():
        comments_list.append({
            "id": c.id,
            "user_id": c.user.id,
            "author": c.user.public_name,
            "profile_pic": c.user.profile_pic,
            "content": c.content,
            "time_ago": _time_ago(c.created_at),
        })
    return render_template("post.html", post=_post_to_dict(post), comments=comments_list)


@main.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    """Create a new comment on a post and update the cached count."""
    post = Post.query.get_or_404(post_id)
    content = request.form.get("content", "").strip()
    if content:
        comment = Comment(post_id=post.id, user_id=current_user.id, content=content)
        db.session.add(comment)
        db.session.flush()
        post.comments_count = post.comments.count()
        db.session.commit()
        flash("Comment posted!", "success")
    return redirect(url_for("main.post_detail", post_id=post_id))


@main.route("/post/<int:post_id>/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(post_id, comment_id):
    """Delete the authenticated user's own comment and refresh the count."""
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        flash("You can only delete your own comments.", "danger")
        return redirect(url_for("main.post_detail", post_id=post_id))

    post = Post.query.get_or_404(post_id)
    db.session.delete(comment)
    db.session.flush()
    post.comments_count = post.comments.count()
    db.session.commit()
    flash("Comment deleted.", "success")
    return redirect(url_for("main.post_detail", post_id=post_id))


@main.route("/post/<int:post_id>/vote", methods=["POST"])
@login_required
def vote_post(post_id):
    """Handle upvote/downvote toggle via JSON request and return new totals."""
    post = Post.query.get_or_404(post_id)

    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if action not in ["up", "down"]:
        return jsonify({
            "success": False,
            "error": "Invalid vote action"
        }), 400

    vote_value = 1 if action == "up" else -1

    existing_vote = Vote.query.filter_by(
        post_id=post.id,
        user_id=current_user.id
    ).first()

    if existing_vote is None:
        new_vote = Vote(
            post_id=post.id,
            user_id=current_user.id,
            value=vote_value
        )
        db.session.add(new_vote)
        post.votes += vote_value

    elif existing_vote.value == vote_value:
        post.votes -= existing_vote.value
        db.session.delete(existing_vote)

    else:
        post.votes -= existing_vote.value
        existing_vote.value = vote_value
        post.votes += vote_value

    db.session.commit()

    return jsonify({
        "success": True,
        "votes": post.votes,
        "user_voted": _get_user_vote(post.id, current_user.id),
    })



@main.route("/api/fetch-news", methods=["POST"])
@login_required
def trigger_news_fetch():
    """Manual trigger to run a news cycle (for testing/admin use)."""
    from app.news_service import run_news_cycle
    from flask import current_app
    run_news_cycle(current_app._get_current_object())
    flash("News cycle triggered! New posts should appear shortly.", "success")
    return redirect(url_for("main.index"))


@main.route("/signup", methods=["GET", "POST"])
def signup():
    """Show the registration form (GET) or create a new user account (POST)."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = SignUpForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash("This email is already registered.", "danger")
            return redirect(url_for("main.signup"))

        user = User(
            name=form.name.data,
            display_name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please sign in.", "success")
        return redirect(url_for("main.signin"))

    return render_template("signup.html", form=form)


@main.route("/signin", methods=["GET", "POST"])
def signin():
    """Show the sign-in form (GET) or authenticate the user (POST)."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    
    form = SignInForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("main.signin"))

        login_user(user, remember=form.remember.data)

        flash("Signed in successfully.", "success")
        return redirect(url_for("main.index"))

    return render_template("signin.html", form=form)



# Human-readable metadata for each bot style (used on the bots page)
BOT_STYLES = [
    {"key": "satire", "icon": "emoji-laughing", "name": "Satire", "description": "Dry wit and parody on current events."},
    {"key": "meme", "icon": "lightning-charge-fill", "name": "Meme", "description": "Relatable, humorous internet-style posts."},
    {"key": "breaking", "icon": "megaphone", "name": "Breaking", "description": "Urgent tone for fast-moving news."},
    {"key": "wholesome", "icon": "heart", "name": "Wholesome", "description": "Positive, uplifting stories."},
    {"key": "question", "icon": "question-circle", "name": "Question", "description": "Thought-provoking open questions."},
    {"key": "anger", "icon": "fire", "name": "Anger", "description": "Hot takes and strong opinions."},
]


@main.route("/api/bots/<bot_name>/toggle", methods=["POST"])
@login_required
def toggle_bot(bot_name):
    """Toggle the active/paused state of a bot for the authenticated user."""
    bot = Bot.query.filter_by(name=bot_name).first_or_404()
    bot.active = not bot.active
    db.session.commit()
    return jsonify({"active": bot.active})


@main.route("/bots")
def bots():
    """List all AI bot personas with their post counts and vote totals."""
    all_bots = Bot.query.all()
    style_descriptions = {style["key"]: style["description"] for style in BOT_STYLES}
    bot_list = []
    for b in all_bots:
        post_count = b.posts.count()
        total_votes = db.session.query(db.func.coalesce(db.func.sum(Post.votes), 0)).filter(Post.bot_id == b.id).scalar()
        last_post_obj = b.posts.order_by(Post.created_at.desc()).first()
        bot_list.append({
            "name": b.name,
            "style": b.style,
            "style_icon": b.style_icon,
            "description": b.description,
            "style_description": style_descriptions.get(b.style, ""),
            "posts": post_count,
            "votes": total_votes,
            "last_post": _time_ago(last_post_obj.created_at) if last_post_obj else "never",
            "active": b.active if current_user.is_authenticated else True,
        })
    total_posts = sum(b["posts"] for b in bot_list)
    total_votes = sum(b["votes"] for b in bot_list)
    return render_template(
        "bots.html",
        bots=bot_list,
        total_posts=total_posts,
        total_votes=total_votes,
    )




@main.route("/account")
@login_required
def account():
    """Render the authenticated user's account page (profile + activity)."""
    user_vote_count = Vote.query.filter_by(user_id=current_user.id).count()
    user_comment_count = Comment.query.filter_by(user_id=current_user.id).count()

    interacted_bot_count = (
        Bot.query
        .join(Post)
        .outerjoin(Vote, Vote.post_id == Post.id)
        .outerjoin(Comment, Comment.post_id == Post.id)
        .filter(
            db.or_(
                Vote.user_id == current_user.id,
                Comment.user_id == current_user.id
            )
        )
        .distinct()
        .count()
    )

    stats = [
        {"label": "Votes", "value": user_vote_count},
        {"label": "Comments", "value": user_comment_count},
        {"label": "Interacted Bots", "value": interacted_bot_count},
    ]
    
    voted_posts = (
        Post.query
        .join(Vote, Vote.post_id == Post.id)
        .filter(Vote.user_id == current_user.id)
        .order_by(Vote.created_at.desc())
        .all()
    )

    commented_posts = (
        Post.query
        .join(Comment, Comment.post_id == Post.id)
        .filter(Comment.user_id == current_user.id)
        .distinct()
        .order_by(Post.created_at.desc())
        .all()
    )

    form = ProfileForm(obj=current_user)

    return render_template(
        "account.html",
        user=current_user,
        stats=stats,
        form=form,
        voted_posts=voted_posts,
        commented_posts=commented_posts,
    )


@main.route("/account/profile", methods=["POST"])
@login_required
def update_profile():
    """Validate and persist changes to the user's profile details."""
    form = ProfileForm()

    if not form.validate_on_submit():
        flash("Please check your profile details.", "danger")
        return redirect(url_for("main.account"))

    existing_user = User.query.filter(
        User.email == form.email.data,
        User.id != current_user.id
    ).first()

    if existing_user:
        flash("This email is already used by another account.", "danger")
        return redirect(url_for("main.account"))

    current_user.display_name = form.display_name.data
    current_user.bio = form.bio.data or ""
    current_user.website = form.website.data or ""
    current_user.email = form.email.data

    db.session.commit()

    flash("Profile updated successfully.", "success")
    return redirect(url_for("main.account"))


@main.route("/account/profile-pic", methods=["POST"])
@login_required
def upload_profile_pic():
    """Accept an uploaded image, save it, and set it as the user's avatar."""
    file = request.files.get("profile_pic")
    if not file or file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("main.account"))

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_PIC_EXTENSIONS:
        flash("Invalid file type. Use PNG, JPG, GIF, or WebP.", "danger")
        return redirect(url_for("main.account"))

    upload_dir = os.path.join(current_app.static_folder, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    if current_user.profile_pic:
        old_path = os.path.join(current_app.static_folder, current_user.profile_pic)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(upload_dir, filename))
    current_user.profile_pic = f"uploads/avatars/{filename}"
    db.session.commit()

    flash("Profile picture updated.", "success")
    return redirect(url_for("main.account"))


@main.route("/account/profile-pic/delete", methods=["POST"])
@login_required
def delete_profile_pic():
    """Remove the user's profile picture and delete the file from disk."""
    if current_user.profile_pic:
        old_path = os.path.join(current_app.static_folder, current_user.profile_pic)
        if os.path.exists(old_path):
            os.remove(old_path)
        current_user.profile_pic = ""
        db.session.commit()
        flash("Profile picture removed.", "success")
    return redirect(url_for("main.account"))


@main.route("/user/<int:user_id>")
def user_profile(user_id):
    """Display a public user profile with their voted and commented posts."""
    profile_user = User.query.get_or_404(user_id)

    voted_posts = (
        Post.query
        .join(Vote, Vote.post_id == Post.id)
        .filter(Vote.user_id == profile_user.id)
        .order_by(Vote.created_at.desc())
        .all()
    )

    commented_posts = (
        Post.query
        .join(Comment, Comment.post_id == Post.id)
        .filter(Comment.user_id == profile_user.id)
        .distinct()
        .order_by(Post.created_at.desc())
        .all()
    )

    return render_template(
        "user_profile.html",
        profile_user=profile_user,
        voted_posts=voted_posts,
        commented_posts=commented_posts,
    )
    

@main.route("/guidelines")
def guidelines():
    """Render the static community guidelines page."""
    return render_template("guidelines.html")


@main.route("/logout")
@login_required
def logout():
    """Log the current user out and redirect to the sign-in page."""
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.signin"))

