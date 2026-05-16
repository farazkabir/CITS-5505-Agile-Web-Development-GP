import unittest
from app import create_app, db
from app.models import User, Bot, Post, Vote, Comment


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False
    NEWS_FETCH_INTERVAL = 9999
    NEWSAPI_KEY = ""
    GEMINI_API_KEY = ""


class BaseTestCase(unittest.TestCase):
    """Shared setup: creates an in-memory DB and seeds a test user + bot."""

    def setUp(self):
        self.app = create_app()
        self.app.config.from_object(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.user = User(name="Test User", display_name="Tester", email="test@example.com")
        self.user.set_password("password123")
        db.session.add(self.user)

        self.bot = Bot(name="TestBot", style="satire", style_icon="emoji-laughing", description="A test bot")
        db.session.add(self.bot)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login(self, email="test@example.com", password="password123"):
        return self.client.post("/signin", data={
            "email": email,
            "password": password,
        }, follow_redirects=True)


# ── Test 1: User password hashing ─────────────────────────────────────────────
class TestUserPassword(BaseTestCase):
    def test_password_hash_and_verify(self):
        """Correct password returns True, wrong password returns False."""
        self.assertTrue(self.user.check_password("password123"))
        self.assertFalse(self.user.check_password("wrongpassword"))


# ── Test 2: public_name fallback ──────────────────────────────────────────────
class TestPublicNameFallback(BaseTestCase):
    def test_public_name_falls_back_to_name(self):
        """public_name returns display_name when set, otherwise falls back to name."""
        self.assertEqual(self.user.public_name, "Tester")

        self.user.display_name = None
        self.assertEqual(self.user.public_name, "Test User")


# ── Test 3: Post.make_hash determinism ────────────────────────────────────────
class TestPostMakeHash(BaseTestCase):
    def test_same_inputs_produce_same_hash(self):
        """Identical URL + bot name always yields the same hash."""
        h1 = Post.make_hash("https://example.com/article", "TestBot")
        h2 = Post.make_hash("https://example.com/article", "TestBot")
        self.assertEqual(h1, h2)

    def test_different_inputs_produce_different_hash(self):
        """Different URL or bot name yields a different hash."""
        h1 = Post.make_hash("https://example.com/a", "BotA")
        h2 = Post.make_hash("https://example.com/a", "BotB")
        self.assertNotEqual(h1, h2)


# ── Test 4: Sign-up creates a new user ────────────────────────────────────────
class TestSignUp(BaseTestCase):
    def test_signup_creates_user(self):
        """POST /signup with valid data creates a user and redirects to sign-in."""
        resp = self.client.post("/signup", data={
            "name": "New Person",
            "email": "new@example.com",
            "password": "securepass1",
            "confirm_password": "securepass1",
            "terms": True,
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        user = User.query.filter_by(email="new@example.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.display_name, "New Person")


# ── Test 5: Sign-in with valid credentials ────────────────────────────────────
class TestSignIn(BaseTestCase):
    def test_signin_succeeds(self):
        """Signing in with correct credentials redirects to the feed."""
        resp = self.login()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"NewsPulse", resp.data)

    def test_signin_wrong_password(self):
        """Signing in with wrong password shows an error."""
        resp = self.login(password="wrong")
        self.assertIn(b"Invalid email or password", resp.data)


# ── Test 6: Voting on a post (upvote / toggle) ───────────────────────────────
class TestVoting(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.post = Post(
            bot_id=self.bot.id,
            title="Test Post",
            content="Some content",
            source_hash=Post.make_hash("https://example.com/test", self.bot.name),
        )
        db.session.add(self.post)
        db.session.commit()

    def test_upvote_increments_score(self):
        """An upvote increases the post score by 1."""
        self.login()
        resp = self.client.post(
            f"/post/{self.post.id}/vote",
            json={"action": "up"},
        )
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["votes"], 1)
        self.assertEqual(data["user_voted"], "up")

    def test_upvote_toggle_removes_vote(self):
        """Upvoting the same post twice removes the vote."""
        self.login()
        self.client.post(f"/post/{self.post.id}/vote", json={"action": "up"})
        resp = self.client.post(f"/post/{self.post.id}/vote", json={"action": "up"})
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["votes"], 0)
        self.assertIsNone(data["user_voted"])


if __name__ == "__main__":
    unittest.main()
