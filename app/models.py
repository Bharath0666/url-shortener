"""
SQLAlchemy ORM models for the URL Shortener.
"""

from datetime import datetime, timezone
from app import db


class Url(db.Model):
    """Shortened URL record."""

    __tablename__ = "urls"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    click_count = db.Column(db.BigInteger, nullable=False, default=0)

    # Relationship
    click_logs = db.relationship(
        "ClickLog", backref="url", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self, base_url: str = "") -> dict:
        """Serialize to JSON-friendly dict."""
        return {
            "id": self.id,
            "short_code": self.short_code,
            "short_url": f"{base_url}/{self.short_code}" if base_url else self.short_code,
            "original_url": self.original_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "click_count": self.click_count,
        }


class ClickLog(db.Model):
    """Individual click / visit record for analytics."""

    __tablename__ = "click_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    url_id = db.Column(
        db.BigInteger, db.ForeignKey("urls.id", ondelete="CASCADE"), nullable=False
    )
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text, nullable=True)
    referer = db.Column(db.Text, nullable=True)
    clicked_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "referer": self.referer,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
        }
