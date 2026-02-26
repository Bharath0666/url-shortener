"""
Application configuration — loaded from .env
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

    # ---- Database ----
    # Render injects DATABASE_URL for PostgreSQL.
    # Render still uses the old "postgres://" prefix — SQLAlchemy needs "postgresql://".
    _raw_db_url = os.getenv("DATABASE_URL", "")
    if _raw_db_url:
        SQLALCHEMY_DATABASE_URI = _raw_db_url.replace(
            "postgres://", "postgresql://", 1
        )
    else:
        # Fallback: build MySQL URI from individual env vars (local dev)
        MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
        MYSQL_USER = os.getenv("MYSQL_USER", "root")
        MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
        MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "url_shortener")
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
            f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
            "?charset=utf8mb4"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Redis ----
    # Render injects REDIS_URL for its managed Redis instance.
    REDIS_URL = os.getenv("REDIS_URL", "")
    if not REDIS_URL:
        REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_DB = int(os.getenv("REDIS_DB", 0))
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # App
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

    # Rate Limiter storage
    RATELIMIT_STORAGE_URI = REDIS_URL
    RATELIMIT_STRATEGY = "fixed-window"
