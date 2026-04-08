"""
System API Blueprint.

Handles system stats, logs, config management, and health checks.
"""

import os
import psutil
import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    rpc_manager = current_app.config["rpc_manager"]

    try:
        sync_status = rpc_manager.get_sync_status()

        ordexcoind_connected = sync_status.get("ordexcoind", {}).get("connected", False)
        ordexgoldd_connected = sync_status.get("ordexgoldd", {}).get("connected", False)

        db = current_app.config["db_manager"].get_db()
        has_wallet = db.has_wallet()

        return jsonify(
            {
                "status": "healthy"
                if (ordexcoind_connected and ordexgoldd_connected)
                else "degraded",
                "daemons": {
                    "ordexcoind": ordexcoind_connected,
                    "ordexgoldd": ordexgoldd_connected,
                },
                "wallet_ready": has_wallet,
                "timestamp": int(os.times().real * 1000),
            }
        )

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@system_bp.route("/stats", methods=["GET"])
def get_system_stats():
    """Get system statistics."""
    try:
        disk_usage = psutil.disk_usage("/")
        memory = psutil.virtual_memory()
        network = psutil.net_io_counters()

        config_gen = current_app.config["config_generator"]
        ordexcoind_config = config_gen.get_daemon_config("ordexcoind")
        ordexgold_config = config_gen.get_daemon_config("ordexgoldd")

        return jsonify(
            {
                "disk": {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "percent": disk_usage.percent,
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                },
                "daemon_config": {
                    "ordexcoind": ordexcoind_config,
                    "ordexgoldd": ordexgold_config,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/logs", methods=["GET"])
def get_logs():
    """Get audit logs."""
    level = request.args.get("level")
    category = request.args.get("category")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    db = current_app.config["db_manager"].get_db()

    try:
        logs = db.get_audit_logs(level, category, limit, offset)

        return jsonify({"logs": logs, "count": len(logs)})

    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/config", methods=["GET"])
def get_daemon_config():
    """Get daemon configuration."""
    config_gen = current_app.config["config_generator"]

    try:
        ordexcoind_config = config_gen.get_daemon_config("ordexcoind")
        ordexgold_config = config_gen.get_daemon_config("ordexgoldd")

        return jsonify(
            {"ordexcoind": ordexcoind_config, "ordexgoldd": ordexgold_config}
        )

    except Exception as e:
        logger.error(f"Error getting daemon config: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/config", methods=["POST"])
def update_daemon_config():
    """Update daemon configuration."""
    daemon = request.json.get("daemon")
    updates = request.json.get("config", {})

    if daemon not in ["ordexcoind", "ordexgoldd"]:
        return jsonify({"error": "Invalid daemon"}), 400

    validation_service = current_app.config["validation_service"]
    result = validation_service.validate_config(updates)

    if not result.valid:
        return jsonify(
            {
                "errors": [
                    {"field": k, "message": v.message}
                    for e in result.errors
                    for k, v in {"config": e}.items()
                ]
            }
        ), 400

    config_gen = current_app.config["config_generator"]

    try:
        config_gen.update_daemon_config(daemon, updates)

        db = current_app.config["db_manager"].get_db()
        db.add_audit_log("INFO", "config", f"Updated {daemon} config", updates)

        return jsonify({"success": True, "message": f"{daemon} configuration updated"})

    except Exception as e:
        logger.error(f"Error updating daemon config: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/rpc-console", methods=["POST"])
def rpc_console():
    """Execute RPC command (for debugging)."""
    command = request.json.get("command")
    params = request.json.get("params", [])
    daemon = request.json.get("daemon", "ordexcoind")

    if not command:
        return jsonify({"error": "Command required"}), 400

    rpc_manager = current_app.config["rpc_manager"]

    try:
        rpc_client = rpc_manager.get_client(daemon)
        result = rpc_client.call(command, *params)

        return jsonify({"success": True, "result": result})

    except Exception as e:
        logger.error(f"Error executing RPC command: {e}")
        return jsonify({"error": str(e)}), 500
