from flask import Blueprint, request, jsonify
import logging

from ordex_web_wallet.database import get_user_wallets, DATABASE
from ordex_web_wallet.middleware.auth import require_auth, get_current_user_guid
from ordex_web_wallet.rpc import daemon_manager, sanitize_rpc_error
from ordex_web_wallet.app import logger
from ordex_web_wallet.utils.validation import (
    is_valid_address,
    is_valid_amount,
    sanitize_label,
)
from ordex_web_wallet.utils.logging_utils import log_wallet

wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/balance", methods=["GET"])
@require_auth
def get_balance():
    user_guid = get_current_user_guid()
    wallets = get_user_wallets(user_guid)

    balances = {}
    for wallet in wallets:
        try:
            balance = daemon_manager.get_user_balance(user_guid, wallet["chain"])
            balances[wallet["chain"]] = balance
        except Exception as e:
            balances[wallet["chain"]] = 0.0
            log_wallet(
                "balance_check",
                user_guid=user_guid,
                chain=wallet["chain"],
                success=False,
                error=str(e),
            )

    return jsonify(balances)


@wallet_bp.route("/addresses", methods=["GET"])
@require_auth
def get_addresses():
    user_guid = get_current_user_guid()
    wallets = get_user_wallets(user_guid)

    addresses = {}
    for wallet in wallets:
        try:
            # Use get_or_create_user_address to prefer existing addresses
            address = daemon_manager.get_or_create_user_address(
                user_guid, wallet["chain"]
            )
            addresses[wallet["chain"]] = address
        except Exception as e:
            addresses[wallet["chain"]] = None
            logger.error(
                f"Address error for user {user_guid} on {wallet['chain']}: {str(e)}"
            )

    return jsonify(addresses)


@wallet_bp.route("/send", methods=["POST"])
@require_auth
def send():
    user_guid = get_current_user_guid()
    data = request.get_json()

    chain = data.get("chain", "ordexcoin")
    to_address = data.get("address", "")
    amount = data.get("amount", 0)

    if not is_valid_address(to_address, chain):
        return jsonify({"error": f"Invalid {chain} address format"}), 400

    if not is_valid_amount(amount):
        return jsonify(
            {"error": "Valid positive amount required (max 8 decimals)"}
        ), 400

    amount = float(amount)

    try:
        txid = daemon_manager.send_from_user(user_guid, chain, to_address, amount)

        DATABASE.execute_write(
            "INSERT INTO transactions (user_guid, txid, chain, amount, type) VALUES (%s, %s, %s, %s, %s)",
            (user_guid, txid, chain, amount, "send"),
        )

        log_wallet(
            "send",
            user_guid=user_guid,
            chain=chain,
            success=True,
            txid=txid,
            amount=amount,
            to_address=to_address[:10] + "...",
        )

        return jsonify({"txid": txid})
    except Exception as e:
        log_wallet(
            "send",
            user_guid=user_guid,
            chain=chain,
            success=False,
            error=sanitize_rpc_error(e),
        )
        return jsonify({"error": sanitize_rpc_error(e)}), 500


@wallet_bp.route("/history", methods=["GET"])
@require_auth
def get_history():
    user_guid = get_current_user_guid()
    chain = request.args.get("chain", "ordexcoin")
    limit = int(request.args.get("limit", 50))

    from ordex_web_wallet.database import DATABASE

    txs = DATABASE.execute(
        """SELECT txid, amount, type, timestamp 
           FROM transactions 
           WHERE user_guid = %s AND chain = %s 
           ORDER BY timestamp DESC LIMIT %s""",
        (user_guid, chain, limit),
    )

    return jsonify([dict(tx) for tx in txs])


@wallet_bp.route("/transactions", methods=["GET"])
@require_auth
def get_transactions():
    user_guid = get_current_user_guid()
    chain = request.args.get("chain")
    limit = int(request.args.get("limit", 50))

    query = "SELECT * FROM transactions WHERE user_guid = %s"
    params = [user_guid]

    if chain:
        query += " AND chain = %s"
        params.append(chain)

    query += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)

    txs = DATABASE.execute(query, tuple(params))
    return jsonify([dict(tx) for tx in txs])


@wallet_bp.route("/address-book", methods=["GET"])
@require_auth
def get_address_book():
    user_guid = get_current_user_guid()
    addresses = DATABASE.execute(
        "SELECT * FROM address_book WHERE user_guid = %s ORDER BY created_at DESC",
        (user_guid,),
    )
    return jsonify([dict(a) for a in addresses])


@wallet_bp.route("/addresses/generate", methods=["POST"])
@require_auth
def generate_address():
    user_guid = get_current_user_guid()
    data = request.get_json()
    chain = data.get("chain", "ordexcoin")
    label = data.get("label", "")

    from ordex_web_wallet.database import get_user_wallets

    wallets = get_user_wallets(user_guid)
    has_wallet = any(w["chain"] == chain for w in wallets)

    if not has_wallet:
        return jsonify(
            {"error": f"No wallet registered for {chain}. Please contact support."}
        ), 400

    try:
        address = daemon_manager.get_or_create_user_address(user_guid, chain)

        if label:
            clean_label = sanitize_label(label)
            DATABASE.execute_write(
                "INSERT INTO address_book (user_guid, label, address, chain) VALUES (%s, %s, %s, %s)",
                (user_guid, clean_label, address, chain),
            )

        return jsonify({"address": address})
    except Exception as e:
        return jsonify({"error": sanitize_rpc_error(e)}), 500


@wallet_bp.route("/addresses/<int:addr_id>/archive", methods=["POST"])
@require_auth
def archive_address(addr_id):
    user_guid = get_current_user_guid()
    DATABASE.execute_write(
        "UPDATE address_book SET archived = TRUE WHERE id = %s AND user_guid = %s",
        (addr_id, user_guid),
    )
    return jsonify({"message": "Address archived"})


@wallet_bp.route("/import-wif", methods=["POST"])
@require_auth
def import_wif():
    user_guid = get_current_user_guid()
    data = request.get_json()
    chain = data.get("chain", "ordexcoin")
    wif = data.get("wif", "")
    passphrase = data.get("passphrase", "")

    if not wif:
        return jsonify({"error": "WIF key required"}), 400

    try:
        txid = daemon_manager.import_wif(user_guid, chain, wif, passphrase)
        log_wallet("import_wif", user_guid=user_guid, chain=chain, success=True)
        return jsonify({"imported": True, "txid": txid})
    except Exception as e:
        log_wallet(
            "import_wif",
            user_guid=user_guid,
            chain=chain,
            success=False,
            error=sanitize_rpc_error(e),
        )
        return jsonify({"error": sanitize_rpc_error(e)}), 500


@wallet_bp.route("/export-wif", methods=["POST"])
@require_auth
def export_wif():
    user_guid = get_current_user_guid()
    data = request.get_json()
    chain = data.get("chain", "ordexcoin")

    try:
        wif = daemon_manager.export_wif(user_guid, chain)
        log_wallet("export_wif", user_guid=user_guid, chain=chain, success=True)
        return jsonify({"wif": wif})
    except Exception as e:
        log_wallet(
            "export_wif",
            user_guid=user_guid,
            chain=chain,
            success=False,
            error=sanitize_rpc_error(e),
        )
        return jsonify({"error": sanitize_rpc_error(e)}), 500


@wallet_bp.route("/backup", methods=["POST"])
@require_auth
def backup():
    user_guid = get_current_user_guid()
    data = request.get_json()
    chain = data.get("chain", "ordexcoin")
    try:
        path = daemon_manager.backup_wallet(user_guid, chain)
        log_wallet("backup", user_guid=user_guid, chain=chain, success=True, path=path)
        return jsonify({"message": "Backup created successfully", "path": path})
    except Exception as e:
        log_wallet(
            "backup",
            user_guid=user_guid,
            chain=chain,
            success=False,
            error=sanitize_rpc_error(e),
        )
        return jsonify({"error": sanitize_rpc_error(e)}), 500


@wallet_bp.route("/encrypt", methods=["POST"])
@require_auth
def encrypt():
    user_guid = get_current_user_guid()
    data = request.get_json()
    chain = data.get("chain", "ordexcoin")
    passphrase = data.get("passphrase")
    if not passphrase:
        return jsonify({"error": "Passphrase required"}), 400
    try:
        daemon_manager.encrypt_wallet(user_guid, chain, passphrase)
        return jsonify(
            {"message": "Wallet encrypted successfully. Restart daemon to apply."}
        )
    except Exception as e:
        return jsonify({"error": sanitize_rpc_error(e)}), 500


@wallet_bp.route("/change-passphrase", methods=["POST"])
@require_auth
def change_passphrase():
    user_guid = get_current_user_guid()
    data = request.get_json()
    chain = data.get("chain", "ordexcoin")
    old_pw = data.get("old_passphrase")
    new_pw = data.get("new_passphrase")
    if not old_pw or not new_pw:
        return jsonify({"error": "Old and new passphrases required"}), 400
    try:
        daemon_manager.change_wallet_passphrase(user_guid, chain, old_pw, new_pw)
        return jsonify({"message": "Passphrase changed successfully"})
    except Exception as e:
        return jsonify({"error": sanitize_rpc_error(e)}), 500
