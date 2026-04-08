"""
Transactions API Blueprint.

Handles transaction listing, details, and sending.
"""

import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("", methods=["GET"])
@transactions_bp.route("/", methods=["GET"])
def get_transactions():
    """Get transactions with optional filtering."""
    network = request.args.get("network")
    category = request.args.get("category")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    db = current_app.config["db_manager"].get_db()

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        transactions = db.get_transactions(network, category, limit, offset)
        return jsonify({"transactions": transactions, "count": len(transactions)})

    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({"error": str(e)}), 500


@transactions_bp.route("/<txid>", methods=["GET"])
def get_transaction(txid):
    """Get specific transaction details."""
    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        tx = db.get_transaction(txid)

        if not tx:
            rpc_client = rpc_manager.get_client("ordexcoin")
            try:
                rpc_tx = rpc_client.gettransaction(txid)
                return jsonify(rpc_tx)
            except:
                return jsonify({"error": "Transaction not found"}), 404

        return jsonify(tx)

    except Exception as e:
        logger.error(f"Error getting transaction: {e}")
        return jsonify({"error": str(e)}), 500


@transactions_bp.route("/send", methods=["POST"])
def send_transaction():
    """Send a transaction."""
    validation_service = current_app.config["validation_service"]

    address = request.json.get("address")
    amount = request.json.get("amount")
    network = request.json.get("network", "ordexcoin")
    fee = request.json.get("fee")

    addr_result = validation_service.validate_address(address, network)
    if not addr_result.valid:
        return jsonify(
            {"errors": [{"field": "address", "message": addr_result.errors[0].message}]}
        ), 400

    amount_result = validation_service.validate_amount(amount)
    if not amount_result.valid:
        return jsonify(
            {
                "errors": [
                    {"field": "amount", "message": amount_result.errors[0].message}
                ]
            }
        ), 400

    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        rpc_client = rpc_manager.get_client(network)

        unspent = rpc_client.listunspent(0, 999999)
        if not unspent:
            return jsonify({"error": "No unspent outputs available"}), 400

        total_amount = float(amount)
        inputs = []
        total_in = 0.0

        for utxo in unspent:
            inputs.append({"txid": utxo["txid"], "vout": utxo["vout"]})
            total_in += utxo["amount"]
            if total_in >= total_amount:
                break

        if total_in < total_amount:
            return jsonify({"error": "Insufficient funds"}), 400

        outputs = {address: total_amount}

        change_address = rpc_client.getnewaddress()
        fee_amount = float(fee) if fee else 0.001
        change_amount = total_in - total_amount - fee_amount

        if change_amount > 0.00000001:
            outputs[change_address] = change_amount

        raw_tx = rpc_client.createrawtransaction(inputs, outputs)
        signed_tx = rpc_client.signrawtransaction(raw_tx)

        if not signed_tx.get("complete"):
            return jsonify({"error": "Transaction signing failed"}), 400

        txid = rpc_client.sendrawtransaction(signed_tx["hex"])

        db.add_transaction(
            txid,
            network,
            address,
            -total_amount,
            fee_amount,
            "send",
            time=int(db.get_setting("current_time", "0")) or None,
        )

        db.add_audit_log(
            "INFO", "transaction", f"Sent {total_amount} on {network}", {"txid": txid}
        )

        return jsonify(
            {"success": True, "txid": txid, "amount": total_amount, "fee": fee_amount}
        )

    except Exception as e:
        logger.error(f"Error sending transaction: {e}")
        db.add_audit_log(
            "ERROR", "transaction", f"Failed to send transaction: {str(e)}"
        )
        return jsonify({"error": str(e)}), 500


@transactions_bp.route("/receive", methods=["GET"])
def get_receive_addresses():
    """Get receive addresses."""
    network = request.args.get("network", "ordexcoin")

    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        addresses = db.get_addresses(network, is_change=False)

        if not addresses:
            rpc_client = rpc_manager.get_client(network)
            new_address = rpc_client.getnewaddress()
            db.add_address(new_address, network, "Receive", "default", False)
            addresses = db.get_addresses(network, is_change=False)

        return jsonify({"addresses": addresses})

    except Exception as e:
        logger.error(f"Error getting receive addresses: {e}")
        return jsonify({"error": str(e)}), 500


@transactions_bp.route("/receive/generate", methods=["POST"])
def generate_receive_address():
    """Generate a new receive address."""
    network = request.json.get("network", "ordexcoin")

    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        rpc_client = rpc_manager.get_client(network)
        new_address = rpc_client.getnewaddress()

        label = request.json.get("label", "Receive")
        db.add_address(new_address, network, label, "default", False)

        db.add_audit_log(
            "INFO",
            "address",
            f"Generated new receive address on {network}",
            {"address": new_address},
        )

        return jsonify({"success": True, "address": new_address})

    except Exception as e:
        logger.error(f"Error generating receive address: {e}")
        return jsonify({"error": str(e)}), 500


@transactions_bp.route("/send-addresses", methods=["GET"])
def get_send_addresses():
    """Get send (change) addresses."""
    network = request.args.get("network", "ordexcoin")

    db = current_app.config["db_manager"].get_db()

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        addresses = db.get_addresses(network, is_change=True)

        return jsonify({"addresses": addresses})

    except Exception as e:
        logger.error(f"Error getting send addresses: {e}")
        return jsonify({"error": str(e)}), 500
