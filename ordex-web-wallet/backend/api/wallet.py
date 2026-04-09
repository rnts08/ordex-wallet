from flask import Blueprint, request, jsonify

from ordex_web_wallet.database import get_user_wallets
from ordex_web_wallet.middleware.auth import require_auth, get_current_user_id
from ordex_web_wallet.rpc import daemon_manager

wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/balance", methods=["GET"])
@require_auth
def get_balance():
    user_id = get_current_user_id()
    wallets = get_user_wallets(user_id)

    balances = {}
    for wallet in wallets:
        try:
            balance = daemon_manager.get_user_balance(user_id, wallet["chain"])
            balances[wallet["chain"]] = balance
        except Exception as e:
            balances[wallet["chain"]] = {"error": str(e)}

    return jsonify(balances)


@wallet_bp.route("/addresses", methods=["GET"])
@require_auth
def get_addresses():
    user_id = get_current_user_id()
    wallets = get_user_wallets(user_id)

    addresses = {}
    for wallet in wallets:
        try:
            address = daemon_manager.get_user_address(user_id, wallet["chain"])
            addresses[wallet["chain"]] = address
        except Exception as e:
            addresses[wallet["chain"]] = {"error": str(e)}

    return jsonify(addresses)


@wallet_bp.route("/send", methods=["POST"])
@require_auth
def send():
    user_id = get_current_user_id()
    data = request.get_json()

    chain = data.get("chain", "ordexcoin")
    to_address = data.get("address", "")
    amount = float(data.get("amount", 0))

    if not to_address or amount <= 0:
        return jsonify({"error": "Valid address and amount required"}), 400

    try:
        txid = daemon_manager.send_from_user(user_id, chain, to_address, amount)
        return jsonify({"txid": txid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@wallet_bp.route("/history", methods=["GET"])
@require_auth
def get_history():
    user_id = get_current_user_id()
    chain = request.args.get("chain", "ordexcoin")
    limit = int(request.args.get("limit", 50))

    from ordex_web_wallet.database import DATABASE

    txs = DATABASE.execute(
        """SELECT txid, amount, type, timestamp 
           FROM transactions 
           WHERE user_id = %s AND chain = %s 
           ORDER BY timestamp DESC LIMIT %s""",
        (user_id, chain, limit),
    )

    return jsonify([dict(tx) for tx in txs])
