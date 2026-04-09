from flask import Blueprint, request, jsonify

from ordex_web_wallet.database import (
    get_all_users,
    update_user_status,
    admin_audit_log,
    get_system_stats,
)
from ordex_web_wallet.middleware.auth import require_admin, get_current_user_id

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    users = get_all_users(limit, offset)
    return jsonify([dict(u) for u in users])


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@require_admin
def get_user(user_id):
    from ordex_web_wallet.database import get_user_by_id

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user))


@admin_bp.route("/users/<int:user_id>/disable", methods=["POST"])
@require_admin
def disable_user(user_id):
    update_user_status(user_id, False)
    admin_audit_log(get_current_user_id(), "disable_user", user_id)
    return jsonify({"message": "User disabled"})


@admin_bp.route("/users/<int:user_id>/enable", methods=["POST"])
@require_admin
def enable_user(user_id):
    update_user_status(user_id, True)
    admin_audit_log(get_current_user_id(), "enable_user", user_id)
    return jsonify({"message": "User enabled"})


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_admin
def delete_user(user_id):
    from ordex_web_wallet.database import DATABASE

    DATABASE.execute_write("DELETE FROM users WHERE id = %s", (user_id,))
    admin_audit_log(get_current_user_id(), "delete_user", user_id)
    return jsonify({"message": "User deleted"})


@admin_bp.route("/stats", methods=["GET"])
@require_admin
def get_stats():
    stats = get_system_stats()
    return jsonify(stats)


@admin_bp.route("/fees", methods=["GET"])
@require_admin
def get_fees():
    from ordex_web_wallet.database import DATABASE

    fees = DATABASE.execute("SELECT * FROM fee_config")
    return jsonify([dict(f) for f in fees])


@admin_bp.route("/fees", methods=["POST"])
@require_admin
def set_fees():
    data = request.get_json()
    chain = data.get("chain")
    send_fee = data.get("send_fee_per_kb", 0)
    receive_fee = data.get("receive_fee_percent", 0)

    from ordex_web_wallet.database import DATABASE

    DATABASE.execute_write(
        """INSERT INTO fee_config (chain, send_fee_per_kb, receive_fee_percent)
           VALUES (%s, %s, %s)
           ON CONFLICT (chain) DO UPDATE SET 
             send_fee_per_kb = EXCLUDED.send_fee_per_kb,
             receive_fee_percent = EXCLUDED.receive_fee_percent""",
        (chain, send_fee, receive_fee),
    )
    admin_audit_log(get_current_user_id(), "update_fees", details=data)
    return jsonify({"message": "Fees updated"})
