"""
Selenium end-to-end tests for NewsPulse.

Run with:
    python -m pytest tests/test_selenium.py -v -s
"""

import os
import tempfile
import threading
import time
import unittest

from werkzeug.serving import make_server

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app import create_app, db
from app.models import User, Bot, Post


_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.close(_test_db_fd)


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"

    # These tests are checking user flows, not CSRF protection.
    WTF_CSRF_ENABLED = False

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + _test_db_path
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    NEWSAPI_KEY = ""
    GEMINI_API_KEY = ""
    NEWS_FETCH_INTERVAL = 9999


class ServerThread(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.server = make_server("127.0.0.1", 0, app)
        self.port = self.server.server_port

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


class SeleniumBaseCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)

        with cls.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

            user = User(
                name="Selenium User",
                display_name="Selenium User",
                email="sel@test.com",
            )
            user.set_password("password123")
            db.session.add(user)

            bot = Bot(
                name="TestBot",
                style="satire",
                style_icon="emoji-laughing",
                description="Test bot for Selenium tests.",
                active=True,
            )
            db.session.add(bot)
            db.session.commit()

            post = Post(
                bot_id=bot.id,
                title="Selenium Test Post",
                content="Content for selenium testing.",
                source_url="https://example.com/selenium",
                source_title="Selenium Source",
                source_hash=Post.make_hash("https://example.com/selenium", bot.name),
            )
            db.session.add(post)
            db.session.commit()

            cls.test_post_id = post.id

        cls.server_thread = ServerThread(cls.app)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server_thread.port}"

        time.sleep(0.5)

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,900")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        except Exception:
            pass

        try:
            cls.server_thread.shutdown()
        except Exception:
            pass

        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

        try:
            os.unlink(_test_db_path)
        except OSError:
            pass

    def _set_input_value(self, element_id, value):
        """Set an input value using JavaScript and dispatch input/change events.

        This is more stable than send_keys() in headless Chrome.
        """
        element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, element_id))
        )

        self.driver.execute_script(
            """
            const element = arguments[0];
            const value = arguments[1];

            element.focus();
            element.value = value;

            element.dispatchEvent(new Event("input", { bubbles: true }));
            element.dispatchEvent(new Event("change", { bubbles: true }));
            """,
            element,
            value,
        )

        WebDriverWait(self.driver, 5).until(
            lambda driver: driver.find_element(By.ID, element_id).get_attribute("value")
            == value
        )

    def _set_checkbox(self, element_id, checked=True):
        element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, element_id))
        )

        self.driver.execute_script(
            """
            const element = arguments[0];
            const checked = arguments[1];

            element.checked = checked;

            element.dispatchEvent(new Event("input", { bubbles: true }));
            element.dispatchEvent(new Event("change", { bubbles: true }));
            """,
            element,
            checked,
        )

        WebDriverWait(self.driver, 5).until(
            lambda driver: driver.find_element(By.ID, element_id).is_selected()
            == checked
        )

    def _submit_form(self, css_selector="form"):
        form = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )

        self.driver.execute_script("arguments[0].submit();", form)

    def _signup(self, name, email, password):
        self.driver.get(f"{self.base_url}/signup")

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "name"))
        )

        self._set_input_value("name", name)
        self._set_input_value("email", email)
        self._set_input_value("password", password)
        self._set_input_value("confirm_password", password)
        self._set_checkbox("terms", True)

        self._submit_form("form")

    def _signin(self, email, password):
        self.driver.get(f"{self.base_url}/signin")

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "email"))
        )

        self._set_input_value("email", email)
        self._set_input_value("password", password)

        self._submit_form("form")


class TestSeleniumFlows(SeleniumBaseCase):
    def setUp(self):
        self.driver.delete_all_cookies()

    def test_home_page_loads(self):
        self.driver.get(self.base_url)

        heading = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        self.assertIn("NewsPulse", heading.text)

    def test_signup_redirects_to_signin(self):
        self._signup("New Tester", "newtester@test.com", "securepass1")

        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/signin")
        )

        self.assertIn("/signin", self.driver.current_url)
        self.assertIn("Account created successfully", self.driver.page_source)

    def test_signin_reaches_feed(self):
        self._signin("sel@test.com", "password123")

        WebDriverWait(self.driver, 5).until(
            EC.url_to_be(f"{self.base_url}/")
        )

        self.assertIn("NewsPulse", self.driver.page_source)
        self.assertIn("Selenium Test Post", self.driver.page_source)

    def test_wrong_password_shows_error(self):
        self._signin("sel@test.com", "wrongpassword")

        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/signin")
        )

        flash_msg = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert"))
        ).text

        self.assertTrue(
            "Invalid email or password" in flash_msg
            or "Please check your email and password" in flash_msg
        )

    def test_comment_appears_after_submit(self):
        self._signin("sel@test.com", "password123")

        WebDriverWait(self.driver, 5).until(
            EC.url_to_be(f"{self.base_url}/")
        )

        self.driver.get(f"{self.base_url}/post/{self.test_post_id}")

        textarea = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "content"))
        )

        self.driver.execute_script(
            """
            const textarea = arguments[0];
            textarea.value = "Hello from Selenium!";
            textarea.dispatchEvent(new Event("input", { bubbles: true }));
            textarea.dispatchEvent(new Event("change", { bubbles: true }));
            """,
            textarea,
        )

        WebDriverWait(self.driver, 5).until(
            lambda driver: driver.find_element(By.NAME, "content").get_attribute("value")
            == "Hello from Selenium!"
        )

        self._submit_form("form[action*='/comment']")

        WebDriverWait(self.driver, 5).until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Hello from Selenium!",
            )
        )

        self.assertIn("Hello from Selenium!", self.driver.page_source)

    def test_click_post_opens_detail(self):
        self.driver.get(self.base_url)

        link = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.post-link"))
        )
        link.click()

        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/post/")
        )

        heading = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        self.assertIn("Selenium Test Post", heading.text)


if __name__ == "__main__":
    unittest.main()
