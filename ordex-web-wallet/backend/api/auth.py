import bcrypt
from flask import Blueprint, request, jsonify
from datetime import datetime

from ordex_web_wallet.database import (
    get_user_by_username,
    create_user,
    create_session,
    delete_session,
)
from ordex_web_wallet.middleware.auth import (
    require_auth,
    get_current_user_id,
    create_session_token,
    create_session_expiry,
)
from ordex_web_wallet.rpc import daemon_manager

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    passphrase = data.get("passphrase", "")

    if not username or not email or not password:
        return jsonify({"error": "Username, email and password required"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    existing = get_user_by_username(username)
    if existing:
        return jsonify({"error": "Username already exists"}), 409

    password_hash = hash_password(password)
    user = create_user(username, email, password_hash)
    if not user:
        return jsonify({"error": "Failed to create user"}), 500

    try:
        daemon_manager.create_user_wallet(
            user["id"], "ordexcoin", passphrase or password
        )
        daemon_manager.create_user_wallet(
            user["id"], "ordexgold", passphrase or password
        )
    except Exception as e:
        return jsonify({"error": f"Failed to create wallets: {str(e)}"}), 500
    token = create_session_token()
    expires = create_session_expiry()
    create_session(user["id"], token, expires)

    return jsonify(
        {
            "user_id": user["id"],
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
        return jsonify({"error": "Invalid credentials"}), 401

    if not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    if not user["is_active"]:
        return jsonify({"error": "Account disabled"}), 403

    token = create_session_token()
    expires = create_session_expiry()
    create_session(user["id"], token, expires)

    return jsonify(
        {
            "user_id": user["id"],
            "username": user["username"],
            "is_admin": user["is_admin"],
            "token": token,
        }
    )


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    delete_session(token)
    return jsonify({"message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    user = get_current_user_id()
    return jsonify(
        {
            "user_id": user["user_id"],
            "username": user["username"],
            "is_admin": user["is_admin"],
        }
    )
