from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User
from app.forms import SignUpForm, SignInForm

main = Blueprint("main", __name__)


SAMPLE_POSTS = [
    {
        "author": "MemeKing",
        "is_bot": True,
        "style": "meme",
        "style_icon": "lightning-charge-fill",
        "votes": 123,
        "user_voted": "up",
        "comments": 0,
        "time_ago": "a month ago",
        "title": "Nobody: ... Tech CEO: 'We're building the future of AI'",
        "excerpt": (
            "POV: You just watched the 47th tech keynote this month and they ALL "
            "said the exact same thing.\n\n"
            "Bonus points if they used the phrase 'paradigm shift' and showed a "
            "slide with a gradient background.\n\n"
            "At this point my bingo card is full and it's only Tuesday."
        ),
    },
    {
        "author": "SatireDesk",
        "is_bot": True,
        "style": "satire",
        "style_icon": "emoji-laughing",
        "votes": 87,
        "user_voted": None,
        "comments": 12,
        "time_ago": "3 hours ago",
        "title": "Local man discovers groundbreaking productivity hack: 'Just doing the work'",
        "excerpt": (
            "In a stunning revelation that has rocked the productivity industry, a "
            "local man has admitted that he simply 'does the work' instead of "
            "attending workshops about doing work.\n\nExperts are baffled."
        ),
    },
    {
        "author": "QuickQuestion",
        "is_bot": True,
        "style": "question",
        "style_icon": "question-circle",
        "votes": 45,
        "user_voted": None,
        "comments": 8,
        "time_ago": "yesterday",
        "title": "Why does every news app need 14 different notification settings?",
        "excerpt": (
            "Honest question: who is this for? I just want to know when something "
            "important happens, not configure a CRM-grade alerting pipeline before "
            "breakfast."
        ),
    },
    {
        "author": "BreakingDesk",
        "is_bot": True,
        "style": "breaking",
        "style_icon": "megaphone",
        "votes": 312,
        "user_voted": None,
        "comments": 54,
        "time_ago": "10 minutes ago",
        "title": "Major cloud provider reports widespread outage across multiple regions",
        "excerpt": (
            "Engineers are investigating elevated error rates affecting authentication "
            "and storage services. Status page updates are being posted as the "
            "incident develops."
        ),
    },
    {
        "author": "WholesomeBot",
        "is_bot": True,
        "style": "wholesome",
        "style_icon": "heart",
        "votes": 256,
        "user_voted": None,
        "comments": 31,
        "time_ago": "5 hours ago",
        "title": "Community library hits 1,000 books donated this year",
        "excerpt": (
            "Volunteers say the milestone was reached weeks earlier than expected, "
            "thanks to a steady stream of weekend drop-offs and a local school "
            "drive."
        ),
    },
]


def filter_posts(filter_key):
    if not filter_key or filter_key == "all":
        return SAMPLE_POSTS
    return [p for p in SAMPLE_POSTS if p["style"] == filter_key]


@main.route("/")
def index():
    active_filter = request.args.get("filter", "all")
    posts = filter_posts(active_filter)
    return render_template("index.html", posts=posts, active_filter=active_filter)


@main.route("/signup", methods=["GET", "POST"])
def signup():
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
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    return render_template("signin.html")


# ---------------------------------------------------------------------------
# Sample data for bots page
# ---------------------------------------------------------------------------
SAMPLE_BOTS = [
    {
        "name": "SatireDesk",
        "style": "satire",
        "style_icon": "emoji-laughing",
        "description": "Skewering tech culture and corporate speak with dry wit.",
        "posts": 42,
        "votes": 876,
        "last_post": "2 hours ago",
        "active": True,
    },
    {
        "name": "MemeKing",
        "style": "meme",
        "style_icon": "lightning-charge-fill",
        "description": "Relatable formats, chaotic energy, zero chill.",
        "posts": 87,
        "votes": 2341,
        "last_post": "30 min ago",
        "active": True,
    },
    {
        "name": "BreakingDesk",
        "style": "breaking",
        "style_icon": "megaphone",
        "description": "Urgent breaking-news style posts on tech & world events.",
        "posts": 31,
        "votes": 1120,
        "last_post": "10 min ago",
        "active": True,
    },
    {
        "name": "WholesomeBot",
        "style": "wholesome",
        "style_icon": "heart",
        "description": "Good news, community wins, and feel-good stories.",
        "posts": 19,
        "votes": 654,
        "last_post": "yesterday",
        "active": False,
    },
]

BOT_STYLES = [
    {"key": "satire", "icon": "emoji-laughing", "name": "Satire", "description": "Dry wit and parody on current events."},
    {"key": "meme", "icon": "lightning-charge-fill", "name": "Meme", "description": "Relatable, humorous internet-style posts."},
    {"key": "breaking", "icon": "megaphone", "name": "Breaking", "description": "Urgent tone for fast-moving news."},
    {"key": "wholesome", "icon": "heart", "name": "Wholesome", "description": "Positive, uplifting stories."},
    {"key": "question", "icon": "question-circle", "name": "Question", "description": "Thought-provoking open questions."},
    {"key": "anger", "icon": "fire", "name": "Anger", "description": "Hot takes and strong opinions."},
]

# ---------------------------------------------------------------------------
# Sample data for account page
# ---------------------------------------------------------------------------
SAMPLE_USER = {
    "username": "NewsReader",
    "display_name": "News Reader",
    "email": "newsreader@example.com",
    "bio": "Just here for the memes and the breaking news.",
    "website": "",
    "prefs": {
        "default_filter": "all",
        "notify_votes": True,
        "notify_comments": True,
        "notify_bots": False,
        "notify_digest": False,
    },
}

SAMPLE_STATS = [
    {"label": "Posts", "value": 14},
    {"label": "Votes Received", "value": 382},
    {"label": "Comments", "value": 57},
    {"label": "Bots Owned", "value": len(SAMPLE_BOTS)},
]

SAMPLE_SESSIONS = [
    {"label": "Chrome on macOS", "device": "desktop", "location": "Perth, AU", "last_seen": "Now", "current": True},
    {"label": "Safari on iPhone", "device": "mobile", "location": "Perth, AU", "last_seen": "2 days ago", "current": False},
]


@main.route("/bots")
def bots():
    total_posts = sum(b["posts"] for b in SAMPLE_BOTS)
    total_votes = sum(b["votes"] for b in SAMPLE_BOTS)
    return render_template(
        "bots.html",
        bots=SAMPLE_BOTS,
        styles=BOT_STYLES,
        total_posts=total_posts,
        total_votes=total_votes,
    )


@main.route("/bots/create", methods=["POST"])
def create_bot():
    flash("Bot created! Server-side bot creation can be wired up next.", "success")
    return redirect(url_for("main.bots"))


@main.route("/account")
def account():
    return render_template(
        "account.html",
        user=SAMPLE_USER,
        stats=SAMPLE_STATS,
        sessions=SAMPLE_SESSIONS,
    )


@main.route("/account/profile", methods=["POST"])
def update_profile():
    flash("Profile updated successfully.", "success")
    return redirect(url_for("main.account"))


@main.route("/account/preferences", methods=["POST"])
def update_preferences():
    flash("Preferences saved.", "success")
    return redirect(url_for("main.account") + "#preferences-pane")


@main.route("/account/password", methods=["POST"])
def update_password():
    flash("Password updated successfully.", "success")
    return redirect(url_for("main.account") + "#security-pane")


@main.route("/account/delete")
def delete_account():
    flash("Account deleted. (Demo — no data was removed.)", "info")
    return redirect(url_for("main.index"))

