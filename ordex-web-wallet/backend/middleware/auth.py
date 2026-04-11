import functools
import secrets
from datetime import datetime, timedelta
from flask import request, g, jsonify
from typing import Optional

from ordex_web_wallet.database import get_session, clean_expired_sessions


def get_current_user_guid() -> Optional[str]:
    return getattr(g, "user_guid", None)


def get_current_user() -> Optional[dict]:
    return getattr(g, "user", None)


def is_admin() -> bool:
    return getattr(g, "user", {}).get("is_admin", False)


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token()
        if not token:
            return jsonify({"error": "Authentication required"}), 401

        clean_expired_sessions()
        session = get_session(token)
        if not session:
            return jsonify({"error": "Invalid or expired session"}), 401

        g.user_guid = session["user_guid"]
        g.user = session
        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    @functools.wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if not is_admin():
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated


def extract_token() -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return request.cookies.get("session_token")


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_session_expiry(duration: int = None) -> datetime:
    from ordex_web_wallet.config import config
    from datetime import timezone

    duration = duration or config.SESSION_DURATION
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=duration)
