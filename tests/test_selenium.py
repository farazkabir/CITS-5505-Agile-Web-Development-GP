"""
Selenium end-to-end tests for NewsPulse.

A live Flask development server is started on a background thread (port 5555)
and a headless Chrome browser drives through key user flows: home page load,
sign-up, sign-in, commenting, and post navigation.

Requirements:
    - Google Chrome and a matching ChromeDriver on PATH.
    - ``pip install selenium``

Run with:
    python -m pytest tests/test_selenium.py
"""

import os
import tempfile
import threading
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from app import create_app, db
from app.models import User, Bot, Post

_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.close(_test_db_fd)


class TestConfig:
    """Flask configuration overrides for Selenium tests."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + _test_db_path
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = True
    NEWS_FETCH_INTERVAL = 9999
    NEWSAPI_KEY = ""
    GEMINI_API_KEY = ""
    SERVER_NAME = "127.0.0.1:5555"


class SeleniumBaseCase(unittest.TestCase):
    """Spins up a live Flask server on a background thread for Selenium.

    Seeds one user, one bot, and one post so every test class has data
    to work with.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)

        with cls.app.app_context():
            db.create_all()

            user = User(name="Selenium User", display_name="Selenium User", email="sel@test.com")
            user.set_password("password123")
            db.session.add(user)

            bot = Bot(name="TestBot", style="satire", style_icon="emoji-laughing", description="Test bot")
            db.session.add(bot)
            db.session.commit()

            post = Post(
                bot_id=bot.id,
                title="Selenium Test Post",
                content="Content for selenium testing.",
                source_hash=Post.make_hash("https://example.com/sel", bot.name),
            )
            db.session.add(post)
            db.session.commit()

        cls.server_thread = threading.Thread(
            target=cls.app.run,
            kwargs={"port": 5555, "use_reloader": False},
            daemon=True,
        )
        cls.server_thread.start()

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,900")
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(5)
        cls.base_url = "http://127.0.0.1:5555"

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()
        try:
            os.unlink(_test_db_path)
        except OSError:
            pass

    def _signup(self, name, email, password):
        """Fill and submit the sign-up form with the given credentials."""
        self.driver.get(f"{self.base_url}/signup")
        self.driver.find_element(By.ID, "name").send_keys(name)
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "confirm_password").send_keys(password)
        self.driver.find_element(By.ID, "terms").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    def _signin(self, email, password):
        """Fill and submit the sign-in form with the given credentials."""
        self.driver.get(f"{self.base_url}/signin")
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()


# ── Test 1: Home page loads and shows the brand title ─────────────────────────
class TestHomePage(SeleniumBaseCase):
    def test_home_page_loads(self):
        self.driver.get(self.base_url)
        heading = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertIn("NewsPulse", heading.text)


# ── Test 2: Sign-up form works end-to-end ─────────────────────────────────────
class TestSignUpFlow(SeleniumBaseCase):
    def test_signup_redirects_to_signin(self):
        self._signup("New Tester", "newtester@test.com", "securepass1")
        WebDriverWait(self.driver, 5).until(EC.url_contains("/signin"))
        self.assertIn("/signin", self.driver.current_url)


# ── Test 3: Sign-in with valid credentials reaches the feed ───────────────────
class TestSignInFlow(SeleniumBaseCase):
    def test_signin_reaches_feed(self):
        self._signin("sel@test.com", "password123")
        WebDriverWait(self.driver, 5).until(EC.url_to_be(f"{self.base_url}/"))
        page = self.driver.page_source
        self.assertIn("NewsPulse", page)


# ── Test 4: Sign-in with wrong password shows flash error ─────────────────────
class TestSignInWrongPassword(SeleniumBaseCase):
    def test_wrong_password_shows_error(self):
        self._signin("sel@test.com", "wrongpassword")
        WebDriverWait(self.driver, 5).until(EC.url_contains("/signin"))
        flash_msg = self.driver.find_element(By.CSS_SELECTOR, ".alert").text
        self.assertIn("Invalid email or password", flash_msg)


# ── Test 5: Posting a comment on a post ───────────────────────────────────────
class TestPostComment(SeleniumBaseCase):
    def test_comment_appears_after_submit(self):
        self._signin("sel@test.com", "password123")
        WebDriverWait(self.driver, 5).until(EC.url_to_be(f"{self.base_url}/"))

        self.driver.get(f"{self.base_url}/post/1")
        textarea = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "content"))
        )
        textarea.send_keys("Hello from Selenium!")
        submit_btn = self.driver.find_element(
            By.CSS_SELECTOR, "form[action*='/comment'] button[type='submit']"
        )
        submit_btn.click()

        WebDriverWait(self.driver, 5).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".feed-container"), "Hello from Selenium!")
        )
        page = self.driver.page_source
        self.assertIn("Hello from Selenium!", page)


# ── Test 6: Clicking a post title navigates to the detail page ────────────────
class TestPostNavigation(SeleniumBaseCase):
    def test_click_post_opens_detail(self):
        self.driver.get(self.base_url)
        link = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.post-link"))
        )
        link.click()
        WebDriverWait(self.driver, 5).until(EC.url_contains("/post/"))
        heading = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertIn("Selenium Test Post", heading.text)


if __name__ == "__main__":
    unittest.main()
