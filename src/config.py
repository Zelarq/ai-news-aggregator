import os
from dotenv import load_dotenv

# Load env file
load_dotenv()

class Config:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ai-news-digest-agent:v1.0")
    REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
    REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
    
    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    DIGEST_RECIPIENT = os.getenv("DIGEST_RECIPIENT")
    
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    DB_PATH = os.getenv("DB_PATH", "news_digest.db")

    @classmethod
    def validate(cls, dry_run=False, test_mode=False):
        """Validates that all required configuration parameters are loaded."""
        if test_mode:
            return  # Bypass all checks for mock runs

        errors = []

        # Email credentials are required only for a real (non-dry-run) send
        if not dry_run:
            if not cls.GMAIL_ADDRESS:
                errors.append("GMAIL_ADDRESS is missing")
            if not cls.GMAIL_APP_PASSWORD:
                errors.append("GMAIL_APP_PASSWORD is missing")
            if not cls.DIGEST_RECIPIENT:
                errors.append("DIGEST_RECIPIENT is missing")

        if errors:
            raise ValueError("Configuration Error:\n" + "\n".join(errors))

        # Warn (but don't fail) if optional source credentials are absent
        missing_sources = []
        if not cls.YOUTUBE_API_KEY:
            missing_sources.append("YouTube (YOUTUBE_API_KEY not set)")
        if not (cls.REDDIT_CLIENT_ID and cls.REDDIT_CLIENT_SECRET and
                cls.REDDIT_USERNAME and cls.REDDIT_PASSWORD):
            missing_sources.append("Reddit (credentials not set)")
        if missing_sources:
            import logging
            logging.warning(
                "Optional sources will be skipped: %s. "
                "Hacker News will still run (no key required).",
                ", ".join(missing_sources)
            )
