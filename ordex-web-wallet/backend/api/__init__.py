from flask import Blueprint, jsonify

system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health():
    state = {"status": "healthy", "services": {}}

    try:
        from ordex_web_wallet.rpc import daemon_manager

        oxc_info = daemon_manager.oxc.getblockchaininfo()
        state["services"]["ordexcoind"] = {
            "status": "healthy",
            "blocks": oxc_info.get("blocks", 0),
        }
    except Exception as e:
        state["services"]["ordexcoind"] = {"status": "unhealthy", "error": str(e)}

    try:
        oxg_info = daemon_manager.oxg.getblockchaininfo()
        state["services"]["ordexgoldd"] = {
            "status": "healthy",
            "blocks": oxg_info.get("blocks", 0),
        }
    except Exception as e:
        state["services"]["ordexgoldd"] = {"status": "unhealthy", "error": str(e)}

    try:
        from ordex_web_wallet.database import DATABASE

        DATABASE.execute_one("SELECT 1")
        state["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        state["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        state["status"] = "degraded"

    return jsonify(state)


@system_bp.route("/metrics", methods=["GET"])
def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
