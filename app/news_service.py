"""
Fetches top headlines from NewsAPI and uses Google Gemini to generate
social-media-style posts for each active bot persona.
"""

import json
import time
import random
import logging

import requests
from flask import current_app
from google import genai

from app import db
from app.models import Bot, Post

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"

STYLE_PROMPTS = {
    "satire": (
        "Rewrite this news headline and summary as a satirical social media post. "
        "Use dry wit, irony, and parody. Keep it under 280 characters for the title "
        "and 2-3 short paragraphs for the body."
    ),
    "meme": (
        "Turn this news into a meme-style social media post. Use internet humor, "
        "relatable format (Nobody:... , POV:, etc.), chaotic energy. Keep it punchy."
    ),
    "breaking": (
        "Rewrite this as an urgent breaking-news style post. Use a dramatic, concise "
        "headline and a factual but tense 2-3 sentence summary."
    ),
    "wholesome": (
        "Rewrite this news as a feel-good, uplifting social media post. Emphasize "
        "positivity, community, and hope. Warm tone."
    ),
    "question": (
        "Turn this news into a thought-provoking question post. Frame it as an open "
        "question that invites discussion. Start with 'What if...' or 'Why does...' etc."
    ),
    "anger": (
        "Rewrite this news as an outraged hot-take social media post. Express strong "
        "frustration and disbelief. Keep it passionate but not hateful."
    ),
}


def fetch_headlines(api_key: str, count: int = 10) -> list[dict]:
    """Fetch top headlines from NewsAPI. Returns list of usable article dicts."""
    params = {
        "apiKey": api_key,
        "language": "en",
        "pageSize": min(count * 3, 100),  # fetch extra to filter out bad ones
    }
    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        # Filter out removed/empty articles
        valid = [
            a for a in articles
            if a.get("url")
            and a.get("title")
            and a["title"] != "[Removed]"
            and a.get("description")
            and a["description"] != "[Removed]"
        ]
        return valid[:count]
    except Exception as e:
        logger.error("NewsAPI fetch failed: %s", e)
        return []


def generate_post_content(client, article: dict, style: str) -> dict | None:
    """Use Gemini to transform an article into a styled post."""
    headline = article.get("title", "")
    description = article.get("description", "") or ""
    source_name = article.get("source", {}).get("name", "")

    if not client:
        logger.warning("No Gemini client available — skipping post generation.")
        return None

    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["breaking"])
    user_message = (
        f"Original headline: {headline}\n"
        f"Summary: {description}\n"
        f"Source: {source_name}\n\n"
        f"{prompt}\n\n"
        "Respond ONLY with valid JSON (no markdown, no code fences) with keys: "
        "\"title\" (short catchy headline) and \"content\" (the post body, 2-4 short paragraphs)."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(text)
        return {"title": result.get("title", headline), "content": result.get("content", "")}
    except Exception as e:
        logger.error("Gemini generation failed for style=%s: %s", style, e)
        return None


def run_news_cycle(app=None):
    """
    Main scheduled task: fetch news, assign articles to bots, generate posts.
    Runs inside app context.
    """
    if app is None:
        app = current_app._get_current_object()

    with app.app_context():
        api_key = app.config.get("NEWSAPI_KEY", "")
        gemini_key = app.config.get("GEMINI_API_KEY", "")

        if not api_key or api_key == "your_newsapi_key_here":
            logger.warning("NewsAPI key not configured — skipping news cycle.")
            return

        client = None
        if gemini_key and gemini_key != "your_gemini_key_here":
            client = genai.Client(api_key=gemini_key)
        else:
            logger.info("Gemini key not set — using template-based post generation.")
        active_bots = Bot.query.filter_by(active=True).all()

        if not active_bots:
            logger.info("No active bots — skipping news cycle.")
            return

        articles = fetch_headlines(api_key, count=10)
        if not articles:
            logger.info("No articles fetched — skipping.")
            return

        random.shuffle(articles)
        created = 0

        for article in articles:
            url = article.get("url", "")
            if not url:
                continue

            bot = random.choice(active_bots)
            source_hash = Post.make_hash(url, bot.name)

            try:
                if Post.query.filter_by(source_hash=source_hash).first():
                    continue
            except Exception:
                db.session.rollback()
                continue

            result = generate_post_content(client, article, bot.style)
            if not result:
                continue

            try:
                post = Post(
                    bot_id=bot.id,
                    title=result["title"],
                    content=result["content"],
                    source_url=url,
                    source_title=article.get("title", ""),
                    source_hash=source_hash,
                )
                db.session.add(post)
                db.session.commit()
                created += 1
            except Exception as e:
                db.session.rollback()
                logger.warning("Failed to save post: %s", e)

            time.sleep(5)  # respect Gemini free tier rate limit (15 RPM)

        logger.info("News cycle complete: %d new posts created.", created)
