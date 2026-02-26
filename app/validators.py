"""
Input validation helpers for URL shortener.
"""

import re
from urllib.parse import urlparse

# Maximum length for original URL
MAX_URL_LENGTH = 2048

# Allowed schemes
ALLOWED_SCHEMES = {"http", "https"}

# Basic URL pattern
URL_REGEX = re.compile(
    r"^https?://"                     # scheme
    r"("
    r"([a-zA-Z0-9_-]+\.)+[a-zA-Z]{2,}"  # domain
    r"|localhost"                         # or localhost
    r"|(\d{1,3}\.){3}\d{1,3}"           # or IPv4
    r")"
    r"(:\d+)?"                        # optional port
    r"(/[^\s]*)?$",                   # optional path
    re.IGNORECASE,
)


def validate_url(url: str | None) -> tuple[bool, str]:
    """
    Validate a URL string.

    Returns
    -------
    (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL is required."

    url = url.strip()

    if len(url) > MAX_URL_LENGTH:
        return False, f"URL exceeds maximum length of {MAX_URL_LENGTH} characters."

    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, "URL must start with http:// or https://."

    if not parsed.netloc:
        return False, "URL must contain a valid domain."

    if not URL_REGEX.match(url):
        return False, "URL format is invalid."

    return True, ""


def sanitize_url(url: str) -> str:
    """Strip whitespace and normalize."""
    return url.strip()
