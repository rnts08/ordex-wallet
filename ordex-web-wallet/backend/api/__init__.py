from flask import Blueprint, jsonify
import logging

logger = logging.getLogger("ordex_web_wallet.health")
system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health():
    state = {"status": "healthy", "services": {}, "version": "1.0.1"}

    try:
        from ordex_web_wallet.database import DATABASE

        DATABASE.execute_one("SELECT 1")
        state["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        state["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        state["status"] = "degraded"
        logger.error(f"Health check: database {e}")

    try:
        from ordex_web_wallet.rpc import daemon_manager, sanitize_rpc_error

        info = daemon_manager.get_blockchain_info("ordexcoin")
        state["services"]["ordexcoind"] = {
            "status": "healthy",
            "blocks": int(info.get("blocks", 0)) if info else 0,
            "chain": info.get("chain") if info else None,
        }
    except Exception as e:
        state["services"]["ordexcoind"] = {
            "status": "unhealthy",
            "error": sanitize_rpc_error(e)[:50],
        }
        logger.error(f"Health check: ordexcoind {e}")

    try:
        from ordex_web_wallet.rpc import daemon_manager, sanitize_rpc_error

        info = daemon_manager.get_blockchain_info("ordexgold")
        state["services"]["ordexgoldd"] = {
            "status": "healthy",
            "blocks": int(info.get("blocks", 0)) if info else 0,
            "chain": info.get("chain") if info else None,
        }
    except Exception as e:
        state["services"]["ordexgoldd"] = {
            "status": "unhealthy",
            "error": sanitize_rpc_error(e)[:50],
        }
        logger.error(f"Health check: ordexgoldd {e}")

    try:
        from ordex_web_wallet.database import get_user_count

        state["services"]["users"] = {"status": "healthy", "count": get_user_count()}
    except Exception as e:
        state["services"]["users"] = {"status": "unhealthy", "error": str(e)}

    return jsonify(state)


@system_bp.route("/metrics", methods=["GET"])
def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
