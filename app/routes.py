"""
REST API routes for the URL Shortener.

Endpoints
---------
POST   /api/shorten            — create a short URL
GET    /api/url/<code>         — retrieve URL metadata
GET    /<code>                 — 302 redirect (cached)
GET    /api/analytics/<code>   — click analytics
DELETE /api/url/<code>         — soft-delete a URL
"""

import time
import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, redirect, render_template, current_app
from sqlalchemy import func

from app import db
from app.models import Url, ClickLog
from app.encoder import base62_encode
from app.cache import get_cached_url, set_cached_url, invalidate_cache
from app.validators import validate_url, sanitize_url
from app.rate_limiter import limiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Blueprints
# ---------------------------------------------------------------------------
api_bp = Blueprint("api", __name__, url_prefix="/api")
redirect_bp = Blueprint("redirect", __name__)


# ===========================  DASHBOARD  ===================================

@redirect_bp.route("/")
def index():
    """Serve the single-page dashboard."""
    return render_template("index.html")


# ========================  1. POST /api/shorten  ===========================

@api_bp.route("/shorten", methods=["POST"])
@limiter.limit("30 per minute")
def shorten_url():
    """Create a shortened URL."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    original_url = data.get("url", "").strip()

    # Validate
    is_valid, error_msg = validate_url(original_url)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    original_url = sanitize_url(original_url)

    # Optional expiry (ISO-8601)
    expires_at = None
    if data.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(data["expires_at"])
        except ValueError:
            return jsonify({"error": "expires_at must be a valid ISO-8601 datetime"}), 400

    # ---- Persist to MySQL ----
    # Use a temp short_code that fits VARCHAR(10), then replace after flush
    url_record = Url(original_url=original_url, short_code="tmp", expires_at=expires_at)
    db.session.add(url_record)
    db.session.flush()  # get auto-increment id

    # Generate collision-free short code from the unique id
    short_code = base62_encode(url_record.id)
    url_record.short_code = short_code
    db.session.commit()

    # ---- Write-through to Redis ----
    set_cached_url(short_code, original_url)

    base_url = current_app.config.get("BASE_URL", "")
    return jsonify({
        "message": "URL shortened successfully",
        "data": url_record.to_dict(base_url),
    }), 201


# ====================  2. GET /api/url/<code>  =============================

@api_bp.route("/url/<short_code>", methods=["GET"])
@limiter.limit("100 per minute")
def get_url_info(short_code: str):
    """Return metadata for a short URL."""
    url_record = Url.query.filter_by(short_code=short_code, is_active=True).first()
    if not url_record:
        return jsonify({"error": "Short URL not found"}), 404

    base_url = current_app.config.get("BASE_URL", "")
    return jsonify({"data": url_record.to_dict(base_url)}), 200


# =====================  3. GET /<code>  (redirect)  ========================

@redirect_bp.route("/<short_code>")
@limiter.limit("100 per minute")
def redirect_short_url(short_code: str):
    """Redirect to the original URL.  Uses Redis cache for speed."""
    start = time.perf_counter_ns()

    # --- Try Redis cache first ---
    original_url = get_cached_url(short_code)

    if original_url:
        # Cache hit — still need to log the click asynchronously
        _log_click_and_increment(short_code, request)
        elapsed = (time.perf_counter_ns() - start) / 1_000_000
        logger.info("REDIRECT (cache hit) %s → %s  [%.2f ms]", short_code, original_url, elapsed)
        return redirect(original_url, code=302)

    # --- Cache miss — query MySQL ---
    url_record = Url.query.filter_by(short_code=short_code, is_active=True).first()
    if not url_record:
        return jsonify({"error": "Short URL not found"}), 404

    # Check expiry
    if url_record.expires_at and url_record.expires_at < datetime.now(timezone.utc):
        url_record.is_active = False
        db.session.commit()
        invalidate_cache(short_code)
        return jsonify({"error": "This short URL has expired"}), 404

    original_url = url_record.original_url

    # Populate cache for future hits
    set_cached_url(short_code, original_url)

    # Log click
    _log_click(url_record.id, request)
    url_record.click_count = Url.click_count + 1
    db.session.commit()

    elapsed = (time.perf_counter_ns() - start) / 1_000_000
    logger.info("REDIRECT (db) %s → %s  [%.2f ms]", short_code, original_url, elapsed)
    return redirect(original_url, code=302)


# ================  4. GET /api/analytics/<code>  ===========================

@api_bp.route("/analytics/<short_code>", methods=["GET"])
@limiter.limit("100 per minute")
def get_analytics(short_code: str):
    """Return click analytics for a short URL."""
    url_record = Url.query.filter_by(short_code=short_code, is_active=True).first()
    if not url_record:
        return jsonify({"error": "Short URL not found"}), 404

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # cap

    clicks = (
        ClickLog.query
        .filter_by(url_id=url_record.id)
        .order_by(ClickLog.clicked_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    # Daily breakdown (last 30 days)
    daily_clicks = (
        db.session.query(
            func.date(ClickLog.clicked_at).label("date"),
            func.count(ClickLog.id).label("count"),
        )
        .filter(ClickLog.url_id == url_record.id)
        .group_by(func.date(ClickLog.clicked_at))
        .order_by(func.date(ClickLog.clicked_at).desc())
        .limit(30)
        .all()
    )

    base_url = current_app.config.get("BASE_URL", "")
    return jsonify({
        "data": {
            "url": url_record.to_dict(base_url),
            "total_clicks": url_record.click_count,
            "daily_clicks": [
                {"date": str(row.date), "count": row.count} for row in daily_clicks
            ],
            "recent_clicks": [c.to_dict() for c in clicks.items],
            "pagination": {
                "page": clicks.page,
                "per_page": clicks.per_page,
                "total": clicks.total,
                "pages": clicks.pages,
            },
        }
    }), 200


# ================  5. DELETE /api/url/<code>  ==============================

@api_bp.route("/url/<short_code>", methods=["DELETE"])
@limiter.limit("30 per minute")
def delete_url(short_code: str):
    """Soft-delete a short URL and invalidate cache."""
    url_record = Url.query.filter_by(short_code=short_code, is_active=True).first()
    if not url_record:
        return jsonify({"error": "Short URL not found"}), 404

    url_record.is_active = False
    db.session.commit()

    invalidate_cache(short_code)

    return "", 204


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_click(url_id: int, req) -> None:
    """Insert a click log record."""
    click = ClickLog(
        url_id=url_id,
        ip_address=req.remote_addr or "unknown",
        user_agent=req.headers.get("User-Agent", ""),
        referer=req.headers.get("Referer", ""),
    )
    db.session.add(click)


def _log_click_and_increment(short_code: str, req) -> None:
    """Log click + increment counter (used on cache-hit path)."""
    url_record = Url.query.filter_by(short_code=short_code, is_active=True).first()
    if url_record:
        _log_click(url_record.id, req)
        url_record.click_count = Url.click_count + 1
        db.session.commit()
