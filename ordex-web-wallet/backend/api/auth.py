import bcrypt
import re
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import logging

from ordex_web_wallet.database import (
    get_user_by_username,
    create_user,
    create_session,
    delete_session,
    get_user_wallets,
    create_user_wallet,
    update_user_status,
    delete_user,
)
from ordex_web_wallet.middleware.auth import (
    require_auth,
    require_auth as login_required,
    get_current_user_guid,
    create_session_token,
    create_session_expiry,
)
from ordex_web_wallet.rpc import daemon_manager, sanitize_rpc_error
from ordex_web_wallet.utils.logging_utils import log_auth

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


@auth_bp.route("/register", methods=["POST"])
def register():
    import re
    from datetime import datetime, timedelta

    # Rate limiting check
    rate_key = f"register_rate:{request.remote_addr}"
    # In production, use Redis for rate limiting
    # For now, simple check

    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    passphrase = data.get("passphrase", "")

    # Validate required fields
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # Validate username
    if len(username) < 3 or len(username) > 30:
        return jsonify({"error": "Username must be 3-30 characters"}), 400
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return jsonify(
            {"error": "Username can only contain letters, numbers, and underscore"}
        ), 400

    # Email is optional
    if not email:
        email = None
    elif not re.match(r"^[a-zA-Z0-9_.+-]*@[a-zA-Z0-9-]*\.[a-zA-Z0-9-.]*$", email):
        return jsonify({"error": "Invalid email format"}), 400

    # Validate password strength
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if not re.search(r"[A-Z]", password):
        return jsonify(
            {"error": "Password must contain at least one uppercase letter"}
        ), 400
    if not re.search(r"[a-z]", password):
        return jsonify(
            {"error": "Password must contain at least one lowercase letter"}
        ), 400
    if not re.search(r"\d", password):
        return jsonify({"error": "Password must contain at least one number"}), 400

    # Validate passphrase
    if len(passphrase) < 8:
        return jsonify({"error": "Passphrase must be at least 8 characters"}), 400

    existing = get_user_by_username(username)
    if existing:
        return jsonify({"error": "Username already exists"}), 409

    password_hash = hash_password(password)
    user = create_user(username, email, password_hash)
    if not user:
        log_auth(
            "register", username=username, success=False, error="user_creation_failed"
        )
        return jsonify({"error": "Failed to create user"}), 500

    # Create wallets for new user
    from ordex_web_wallet.app import logger
    from ordex_web_wallet.database import create_user_wallet
    from ordex_web_wallet.rpc import daemon_manager

    passphrase = data.get("passphrase", "")
    for chain in ["ordexcoin", "ordexgold"]:
        try:
            daemon_manager.create_user_wallet(
                None, chain, passphrase or None, user["guid"]
            )
        except Exception as e:
            logger.warning(f"Daemon wallet creation for {chain}: {e}")

        wallet_name = f"wallet_{user['guid']}_{chain}"
        try:
            create_user_wallet(user["guid"], chain, wallet_name)
        except Exception as e:
            logger.error(f"Failed to create wallet DB record for {chain}: {e}")

    token = create_session_token()
    expires = create_session_expiry()
    create_session(user["guid"], token, expires)
    log_auth("register", user_id=user["guid"], username=username, success=True)

    return jsonify(
        {
            "user_id": user["guid"],
            "username": user["username"],
            "token": token,
        }
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = get_user_by_username(username)
    if not user:
        log_auth("login", username=username, success=False, error="user_not_found")
        return jsonify({"error": "Invalid credentials"}), 401

    if not verify_password(password, user["password_hash"]):
        log_auth(
            "login",
            username=username,
            user_id=user.get("guid"),
            success=False,
            error="invalid_password",
        )
        return jsonify({"error": "Invalid credentials"}), 401

    if not user["is_active"]:
        log_auth(
            "login",
            username=username,
            user_id=user.get("guid"),
            success=False,
            error="account_disabled",
        )
        return jsonify({"error": "Account disabled"}), 403

    # Check for missing wallets - create both daemon wallet and DB record
    # Always try to create daemon wallet (will succeed if already exists)
    from ordex_web_wallet.app import logger
    from ordex_web_wallet.database import create_user_wallet
    from ordex_web_wallet.rpc import daemon_manager

    wallets = get_user_wallets(user["guid"])

    for chain in ["ordexcoin", "ordexgold"]:
        try:
            daemon_manager.create_user_wallet(None, chain, None, user["guid"])
        except Exception as e:
            logger.warning(f"Daemon wallet creation for {chain}: {e}")

        if not wallets:
            wallet_name = f"wallet_{user['guid']}_{chain}"
            try:
                create_user_wallet(user["guid"], chain, wallet_name)
                logger.info(f"Created wallet DB record for {chain}")
            except Exception as e:
                logger.error(f"Failed to create wallet DB record for {chain}: {e}")

    token = create_session_token()
    expires = create_session_expiry()
    create_session(user["guid"], token, expires)

    log_auth("login", user_id=user["guid"], username=username, success=True)

    return jsonify(
        {
            "user_id": user["guid"],
            "username": user["username"],
            "is_admin": user["is_admin"],
            "token": token,
        }
    )


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    user_guid = get_current_user_guid()
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    delete_session(token)
    log_auth("logout", user_id=user_id, success=True)
    return jsonify({"message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    user_guid = get_current_user_guid()
    from ordex_web_wallet.database import get_user_by_id

    user = get_user_by_id(user_id)
    return jsonify(
        {
            "user_id": user_id,
            "username": user["username"],
            "is_admin": user["is_admin"],
        }
    )


@auth_bp.route("/2fa/setup", methods=["POST"])
@require_auth
def setup_2fa():
    """Generate 2FA secret for user (future MFA support)."""
    import pyotp

    user_guid = get_current_user_guid()
    secret = pyotp.random_base32()
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=f"OrdexWebWallet", issuer_name="OrdexWebWallet"
    )

    # Store secret temporarily (not enabled until verified)
    from ordex_web_wallet.database import DATABASE

    DATABASE.execute_write(
        "UPDATE users SET two_factor_secret = %s, totp_uris = %s WHERE id = %s",
        (secret, totp_uri, user_id),
    )

    log_auth("2fa_setup", user_id=user_id, success=True)

    return jsonify(
        {
            "secret": secret,
            "totp_uri": totp_uri,
        }
    )


@auth_bp.route("/2fa/enable", methods=["POST"])
@require_auth
def enable_2fa():
    """Enable 2FA after verifying code."""
    import pyotp

    user_guid = get_current_user_guid()
    data = request.get_json()
    code = data.get("code", "")

    from ordex_web_wallet.database import DATABASE

    result = DATABASE.execute_one(
        "SELECT two_factor_secret FROM users WHERE id = %s", (user_id,)
    )

    if not result or not result.get("two_factor_secret"):
        return jsonify({"error": "No 2FA setup found"}), 400

    totp = pyotp.TOTP(result["two_factor_secret"])
    if not totp.verify(code):
        return jsonify({"error": "Invalid verification code"}), 400

    DATABASE.execute_write(
        "UPDATE users SET two_factor_enabled = TRUE WHERE id = %s", (user_id,)
    )

    log_auth("2fa_enable", user_id=user_id, success=True)

    return jsonify({"message": "2FA enabled"})


@auth_bp.route("/2fa/disable", methods=["POST"])
@require_auth
def disable_2fa():
    """Disable 2FA."""
    user_guid = get_current_user_guid()
    data = request.get_json()
    password = data.get("password", "")

    from ordex_web_wallet.database import get_user_by_id, verify_password

    user = get_user_by_id(user_id)

    if not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid password"}), 401

    from ordex_web_wallet.database import DATABASE

    DATABASE.execute_write(
        "UPDATE users SET two_factor_enabled = FALSE, two_factor_secret = NULL, totp_uris = NULL WHERE id = %s",
        (user_id,),
    )

    log_auth("2fa_disable", user_id=user_id, success=True)

    return jsonify({"message": "2FA disabled"})


@auth_bp.route("/2fa/verify", methods=["POST"])
def verify_2fa():
    """Verify 2FA code during login."""
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    code = data.get("code", "")

    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    if user.get("two_factor_enabled"):
        import pyotp

        totp = pyotp.TOTP(user["two_factor_secret"])
        if not totp.verify(code):
            return jsonify({"error": "Invalid 2FA code"}), 401

    token = create_session_token()
    expires = create_session_expiry()
    create_session(user["guid"], token, expires)

    return jsonify(
        {
            "user_id": user["guid"],
            "username": user["username"],
            "is_admin": user["is_admin"],
            "token": token,
        }
    )


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    from ordex_web_wallet.database import get_user_by_id, update_password

    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return jsonify({"error": "Current and new password required"}), 400

    user = get_user_by_id(g.user_id)
    if not verify_password(current_password, user["password_hash"]):
        return jsonify({"error": "Current password is incorrect"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400
    if not re.search(r"[A-Z]", new_password):
        return jsonify(
            {"error": "New password must contain at least one uppercase letter"}
        ), 400
    if not re.search(r"[a-z]", new_password):
        return jsonify(
            {"error": "New password must contain at least one lowercase letter"}
        ), 400
    if not re.search(r"\d", new_password):
        return jsonify({"error": "New password must contain at least one number"}), 400

    new_hash = hash_password(new_password)
    update_password(g.user_id, new_hash)

    return jsonify({"message": "Password changed successfully"})


@auth_bp.route("/settings", methods=["GET"])
@login_required
def get_settings():
    from ordex_web_wallet.database import get_user_by_id

    user = get_user_by_id(g.user_id)
    return jsonify(
        {
            "opt_out_reminders": user.get("opt_out_reminders", False),
            "opt_out_notifications": user.get("opt_out_notifications", False),
            "email": user.get("email"),
            "email_verified": user.get("email_verified", False),
            "last_backup": user.get("last_backup"),
        }
    )


@auth_bp.route("/settings", methods=["POST"])
@login_required
def update_settings():
    from ordex_web_wallet.database import update_user_settings

    data = request.get_json()
    opt_out_reminders = data.get("opt_out_reminders")
    opt_out_notifications = data.get("opt_out_notifications")

    update_user_settings(g.user_id, opt_out_reminders, opt_out_notifications)
    return jsonify({"message": "Settings updated"})


@auth_bp.route("/messages", methods=["GET"])
@login_required
def get_messages():
    from ordex_web_wallet.database import get_user_messages

    messages = get_user_messages(g.user_id)
    unread = get_user_messages(g.user_id, unread_only=True)
    return jsonify(
        {
            "messages": [dict(m) for m in messages],
            "unread_count": len(unread) if unread else 0,
        }
    )


@auth_bp.route("/messages/<int:msg_id>/read", methods=["POST"])
@login_required
def mark_message_read(msg_id):
    mark_message_read(msg_id)
    return jsonify({"message": "Marked as read"})


@auth_bp.route("/delete", methods=["POST"])
@login_required
def delete_account():
    from ordex_web_wallet.database import get_user_by_id

    data = request.get_json()
    password = data.get("password")

    if not password:
        return jsonify({"error": "Password required to delete account"}), 400

    user = get_user_by_id(g.user_id)
    if not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Incorrect password"}), 401

    # Delete Daemon Wallets
    try:
        wallets = get_user_wallets(g.user_id)
        for w in wallets:
            daemon_manager.delete_user_wallet(g.user_id, w["chain"])
    except Exception as e:
        # Log error but proceed with DB deletion
        from ordex_web_wallet.app import logger

        logger.error(
            f"Failed to delete daemon wallets for {user['username']}: {str(e)}"
        )

    # Delete from Database (CASCADE will handle the rest)
    delete_user(g.user_id)

    return jsonify({"message": "Account deleted successfully"})
