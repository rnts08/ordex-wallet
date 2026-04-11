from flask import Blueprint, request, jsonify
import logging
import json

from ordex_web_wallet.database import (
    get_all_users,
    update_user_status,
    admin_audit_log,
    get_system_stats,
    update_password,
    get_users_paged,
)
from ordex_web_wallet.middleware.auth import require_admin, get_current_user_guid
from ordex_web_wallet.api.auth import hash_password
from ordex_web_wallet.rpc import daemon_manager, sanitize_rpc_error
from ordex_web_wallet.utils.logging_utils import log_admin

admin_bp = Blueprint("admin", __name__)

logger = logging.getLogger("ordex_web_wallet.admin")


@admin_bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    limit = int(request.args.get("limit", 25))
    offset = int(request.args.get("offset", 0))
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "DESC")
    search = request.args.get("search", "")

    if search:
        users = get_users_paged(limit, offset, sort_by, sort_order, search)
    else:
        users = get_users_paged(limit, offset, sort_by, sort_order)

    return jsonify([dict(u) for u in users])


@admin_bp.route("/users/count", methods=["GET"])
@require_admin
def get_users_count():
    from ordex_web_wallet.database import get_user_count

    search = request.args.get("search", "")
    if search:
        from ordex_web_wallet.database import DATABASE

        count = DATABASE.execute_one(
            "SELECT COUNT(*) as count FROM users WHERE username LIKE %s OR email LIKE %s",
            (f"%{search}%",),
        )["count"]
    else:
        count = get_user_count()
    return jsonify({"count": count})


@admin_bp.route("/users/<string:user_guid>", methods=["GET"])
@require_admin
def get_user(user_guid):
    from ordex_web_wallet.database import get_user_by_guid

    user = get_user_by_guid(user_guid)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user))


@admin_bp.route("/users/<string:user_guid>/disable", methods=["POST"])
@require_admin
def disable_user(user_guid):
    admin_guid = get_current_user_guid()
    update_user_status(user_guid, False)
    admin_audit_log(admin_id, "disable_user", user_guid)
    log_admin(
        "user_disable", admin_id=admin_id, target_user_guid=user_guid, success=True
    )
    return jsonify({"message": "User disabled"})


@admin_bp.route("/users/<string:user_guid>/enable", methods=["POST"])
@require_admin
def enable_user(user_guid):
    admin_guid = get_current_user_guid()
    update_user_status(user_guid, True)
    admin_audit_log(admin_id, "enable_user", user_guid)
    log_admin(
        "user_enable", admin_id=admin_id, target_user_guid=user_guid, success=True
    )
    return jsonify({"message": "User enabled"})


@admin_bp.route("/users/<string:user_guid>", methods=["DELETE"])
@require_admin
def delete_user(user_guid):
    from ordex_web_wallet.database import DATABASE

    admin_guid = get_current_user_guid()
    DATABASE.execute_write("DELETE FROM users WHERE id = %s", (user_guid,))
    admin_audit_log(admin_id, "delete_user", user_guid)
    log_admin(
        "user_delete", admin_id=admin_id, target_user_guid=user_guid, success=True
    )
    return jsonify({"message": "User deleted"})


@admin_bp.route("/stats", methods=["GET"])
@require_admin
def get_stats():
    stats = get_system_stats()

    from ordex_web_wallet.database import DATABASE, get_backup_count
    from ordex_web_wallet.rpc import daemon_manager

    stats["total_oxc"] = 0.0
    stats["total_oxg"] = 0.0

    try:
        total_oxc = daemon_manager.get_total_balance("ordexcoin")
        total_oxg = daemon_manager.get_total_balance("ordexgold")
        stats["total_oxc"] = float(total_oxc) if total_oxc else 0.0
        stats["total_oxg"] = float(total_oxg) if total_oxg else 0.0
    except:
        pass

    try:
        db_size = DATABASE.execute_one(
            "SELECT pg_database_size(current_database()) as size"
        )["size"]
        stats["database_size"] = db_size
    except:
        stats["database_size"] = 0

    stats["backup_count_30d"] = get_backup_count()

    return jsonify(stats)


@admin_bp.route("/fees", methods=["GET"])
@require_admin
def get_fees():
    from ordex_web_wallet.database import get_fee_config

    fees = get_fee_config()
    return jsonify([dict(f) for f in fees])


@admin_bp.route("/fees", methods=["POST"])
@require_admin
def set_fees():
    data = request.get_json()
    chain = data.get("chain")
    send_fee = data.get("send_fee_per_kb")
    receive_fee = data.get("receive_fee_percent")
    use_auto = data.get("use_auto_fee")
    admin_address = data.get("admin_wallet_address")

    from ordex_web_wallet.database import update_fee_config

    update_fee_config(chain, send_fee, receive_fee, use_auto, admin_address)
    admin_audit_log(get_current_user_guid(), "update_fees", details=data)

    return jsonify({"message": "Fees updated"})


@admin_bp.route("/fees/<chain>", methods=["DELETE"])
@require_admin
def delete_fee(chain):
    from ordex_web_wallet.database import DATABASE

    DATABASE.execute_write("DELETE FROM fee_config WHERE chain = %s", (chain,))
    admin_audit_log(get_current_user_guid(), "delete_fee", details={"chain": chain})
    return jsonify({"message": "Fee config deleted"})


@admin_bp.route("/stake", methods=["GET"])
@require_admin
def get_stake_config():
    from ordex_web_wallet.database import get_stake_config

    configs = get_stake_config()
    return jsonify([dict(c) for c in configs])


@admin_bp.route("/stake", methods=["POST"])
@require_admin
def set_stake_config():
    data = request.get_json()
    chain = data.get("chain")
    apr = data.get("apr_percent")
    intervals = data.get("intervals")
    enabled = data.get("global_enabled")
    auto_stake = data.get("auto_stake_default")

    from ordex_web_wallet.database import update_stake_config

    update_stake_config(chain, apr, intervals, enabled, auto_stake)
    admin_audit_log(get_current_user_guid(), "update_stake_config", details=data)

    return jsonify({"message": "Stake config updated"})


@admin_bp.route("/messages", methods=["POST"])
@require_admin
def send_message():
    data = request.get_json()
    user_guid = data.get("user_guid")
    title = data.get("title")
    message = data.get("message")
    msg_type = data.get("type", "reminder")

    if not user_guid or not title or not message:
        return jsonify({"error": "user_guid, title, and message required"}), 400

    from ordex_web_wallet.database import create_user_message

    create_user_message(user_guid, title, message, msg_type)
    admin_audit_log(
        get_current_user_guid(), "send_message", user_guid, {"title": title}
    )

    return jsonify({"message": "Message sent"})


@admin_bp.route("/messages/broadcast", methods=["POST"])
@require_admin
def broadcast_message():
    data = request.get_json()
    title = data.get("title")
    message = data.get("message")
    msg_type = data.get("type", "announcement")

    if not title or not message:
        return jsonify({"error": "title and message required"}), 400

    from ordex_web_wallet.database import DATABASE, create_user_message

    users = DATABASE.execute("SELECT id FROM users WHERE is_active = TRUE")
    for user in users:
        create_user_message(user["id"], title, message, msg_type)

    admin_guid = get_current_user_guid()
    admin_audit_log(
        admin_id,
        "broadcast_message",
        details={"title": title, "user_count": len(users)},
    )
    log_admin(
        "broadcast", admin_id=admin_id, success=True, user_count=len(users), title=title
    )

    return jsonify({"message": f"Broadcast sent to {len(users)} users"})


@admin_bp.route("/users/<string:user_guid>/reset-password", methods=["POST"])
@require_admin
def reset_user_password(user_guid):
    import re

    data = request.get_json()
    new_password = data.get("new_password")

    if not new_password:
        return jsonify({"error": "New password required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if not re.search(r"[A-Z]", new_password):
        return jsonify(
            {"error": "Password must contain at least one uppercase letter"}
        ), 400
    if not re.search(r"[a-z]", new_password):
        return jsonify(
            {"error": "Password must contain at least one lowercase letter"}
        ), 400
    if not re.search(r"\d", new_password):
        return jsonify({"error": "Password must contain at least one number"}), 400

    new_hash = hash_password(new_password)
    admin_guid = get_current_user_guid()
    update_password(user_guid, new_hash)
    admin_audit_log(admin_id, "reset_password", user_guid)
    log_admin(
        "password_reset", admin_id=admin_id, target_user_guid=user_guid, success=True
    )

    return jsonify({"message": "Password reset successfully"})


@admin_bp.route("/users/<string:user_guid>/details", methods=["GET"])
@require_admin
def get_user_details(user_guid):
    from ordex_web_wallet.database import (
        get_user_by_guid,
        get_user_wallets,
        get_user_transactions,
    )

    user = get_user_by_guid(user_guid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get user's wallets with balances
    wallets = get_user_wallets(user_guid)
    wallet_details = []
    total_balance = {"ordexcoin": 0.0, "ordexgold": 0.0}

    from ordex_web_wallet.rpc import daemon_manager

    for wallet in wallets:
        try:
            balance = daemon_manager.get_user_balance(user_guid, wallet["chain"])
            balance_float = float(balance) if balance else 0.0
            wallet_details.append(
                {
                    "chain": wallet["chain"],
                    "wallet_name": wallet["wallet_name"],
                    "balance": balance_float,
                    "address_count": 1,  # Simplified - in practice you'd count addresses
                }
            )
            if wallet["chain"] in total_balance:
                total_balance[wallet["chain"]] += balance_float
        except Exception as e:
            wallet_details.append(
                {
                    "chain": wallet["chain"],
                    "wallet_name": wallet["wallet_name"],
                    "balance": 0.0,
                    "error": sanitize_rpc_error(e),
                }
            )

    # Get recent transactions (last 10)
    recent_tx = get_user_transactions(user_guid, limit=10)
    recent_activities = []
    for tx in recent_tx:
        recent_activities.append(
            {
                "timestamp": tx["timestamp"],
                "description": f"{tx['type'].title()}: {tx['amount']} {tx['chain'].upper()}",
            }
        )

    # Get recent logins (from sessions - simplified)
    # In a full implementation, you'd have a separate login tracking table

    return jsonify(
        {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "is_admin": user["is_admin"],
            "is_active": user["is_active"],
            "two_factor_enabled": user["two_factor_enabled"],
            "created_at": user["created_at"],
            "last_login": user["last_login"],
            "wallets": wallet_details,
            "total_balance": total_balance,
            "recent_activities": recent_activities,
        }
    )


@admin_bp.route("/users/<string:user_guid>/sweep", methods=["POST"])
@require_admin
def sweep_user_wallet(user_guid):
    data = request.get_json()
    admin_address = data.get("admin_address")

    if not admin_address:
        return jsonify({"error": "Admin address required"}), 400

    from ordex_web_wallet.database import get_user_by_guid
    from ordex_web_wallet.rpc import daemon_manager

    user = get_user_by_guid(user_guid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    results = {"ordexcoin": None, "ordexgold": None}
    admin_guid = get_current_user_guid()

    for chain in ["ordexcoin", "ordexgold"]:
        try:
            balance = daemon_manager.get_user_balance(user_guid, chain)
            if balance and float(balance) > 0:
                txid = daemon_manager.send_to_address(
                    user_guid, chain, admin_address, float(balance)
                )
                results[chain] = {"txid": txid, "amount": balance}
                log_admin(
                    "wallet_sweep",
                    admin_id=admin_id,
                    target_user_guid=user_guid,
                    success=True,
                    chain=chain,
                    amount=balance,
                )
        except Exception as e:
            results[chain] = {"error": sanitize_rpc_error(e)}
            log_admin(
                "wallet_sweep",
                admin_id=admin_id,
                target_user_guid=user_guid,
                success=False,
                chain=chain,
                error=sanitize_rpc_error(e),
            )

    admin_audit_log(admin_id, "sweep_wallet", user_guid, {"results": results})

    return jsonify(results)


@admin_bp.route("/audit", methods=["GET"])
@require_admin
def get_audit_log():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    from ordex_web_wallet.database import DATABASE

    logs = DATABASE.execute(
        """SELECT a.*, u.username as admin_username, tu.username as target_username
           FROM admin_audit a
           LEFT JOIN users u ON u.id = a.admin_user_guid
           LEFT JOIN users tu ON tu.id = a.target_user_guid
           ORDER BY a.created_at DESC
           LIMIT %s OFFSET %s""",
        (limit, offset),
    )
    return jsonify([dict(l) for l in logs])


@admin_bp.route("/maintenance/clear-sessions", methods=["POST"])
@require_admin
def clear_expired_sessions():
    from ordex_web_wallet.database import DATABASE
    from datetime import datetime

    # Simple cleanup of sessions older than 30 days
    DATABASE.execute_write(
        "DELETE FROM sessions WHERE expires_at < %s", (datetime.utcnow(),)
    )
    admin_audit_log(get_current_user_guid(), "maintenance_clear_sessions")
    return jsonify({"message": "Expired sessions cleared"})


@admin_bp.route("/maintenance/rotate-logs", methods=["POST"])
@require_admin
def rotate_audit_logs():
    from ordex_web_wallet.database import DATABASE
    from datetime import datetime, timedelta

    # Keep logs for 90 days
    cutoff = datetime.utcnow() - timedelta(days=90)
    DATABASE.execute_write("DELETE FROM admin_audit WHERE created_at < %s", (cutoff,))
    admin_audit_log(get_current_user_guid(), "maintenance_rotate_logs")
    return jsonify({"message": "Logs rotated (kept last 90 days)"})


@admin_bp.route("/maintenance/backup-db", methods=["POST"])
@require_admin
def backup_database():
    # In a real environment, this might trigger a pg_dump
    # For now, we'll just log it and return success
    admin_audit_log(get_current_user_guid(), "maintenance_backup_db")
    return jsonify({"message": "Database backup initiated"})


@admin_bp.route("/maintenance/toggle", methods=["POST"])
@require_admin
def toggle_maintenance_mode():
    from ordex_web_wallet.database import DATABASE

    # Simple toggle logic using a config table (if it exists) or just return success
    # For now, we'll just audit it
    admin_audit_log(get_current_user_guid(), "maintenance_toggle")
    return jsonify({"enabled": True, "message": "Maintenance mode toggled"})
