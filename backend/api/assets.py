"""
Assets API Blueprint.

Handles asset/balance queries for both networks.
"""

import logging
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

assets_bp = Blueprint("assets", __name__)


@assets_bp.route("", methods=["GET"])
@assets_bp.route("/", methods=["GET"])
def get_assets():
    """Get all assets with balances."""
    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        ordexcoind = rpc_manager.get_client("ordexcoind")
        ordexgoldd = rpc_manager.get_client("ordexgoldd")

        ordexcoin_balance = ordexcoind.getbalance()
        ordexgold_balance = ordexgoldd.getbalance()

        ordexcoin_synced = ordexcoind.get_sync_status()
        ordexgold_synced = ordexgoldd.get_sync_status()

        return jsonify(
            {
                "ordexcoin": {
                    "symbol": "OXC",
                    "name": "OrdexCoin",
                    "balance": ordexcoin_balance,
                    "sync_status": ordexcoin_synced,
                },
                "ordexgold": {
                    "symbol": "OXG",
                    "name": "OrdexGold",
                    "balance": ordexgold_balance,
                    "sync_status": ordexgold_synced,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error getting assets: {e}")
        return jsonify({"error": str(e)}), 500


@assets_bp.route("/<asset>", methods=["GET"])
def get_asset(asset):
    """Get specific asset details."""
    if asset not in ["ordexcoin", "ordexgold"]:
        return jsonify({"error": "Invalid asset"}), 400

    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        rpc_client = rpc_manager.get_client(asset)
        balance = rpc_client.getbalance()
        sync_status = rpc_client.get_sync_status()

        addresses = db.get_addresses(asset)

        return jsonify(
            {"balance": balance, "sync_status": sync_status, "addresses": addresses}
        )

    except Exception as e:
        logger.error(f"Error getting asset {asset}: {e}")
        return jsonify({"error": str(e)}), 500
