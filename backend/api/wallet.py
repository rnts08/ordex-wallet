"""
Wallet API Blueprint.

Handles wallet creation, import, backup, restore, and signing operations.
"""

import logging
import hashlib
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

wallet_bp = Blueprint("wallet", __name__)


def validate_request(schema):
    """Validate request data against schema."""
    validation_service = current_app.config["validation_service"]
    errors = []
    for field, rules in schema.items():
        value = request.json.get(field)
        if rules.get("required") and not value:
            errors.append({"field": field, "message": f"{field} is required"})
            continue
        if value:
            if "type" in rules:
                if rules["type"] == "address":
                    result = validation_service.validate_address(
                        value, rules.get("network", "ordexcoin")
                    )
                elif rules["type"] == "amount":
                    result = validation_service.validate_amount(
                        value, rules.get("allow_zero", False)
                    )
                elif rules["type"] == "private_key":
                    result = validation_service.validate_private_key(
                        value, rules.get("format", "wif")
                    )
                else:
                    continue
                if not result.valid:
                    errors.extend(
                        [{"field": field, "message": e.message} for e in result.errors]
                    )
    return errors


@wallet_bp.route("/create", methods=["POST"])
def create_wallet():
    """Create a new wallet."""
    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if db.has_wallet():
        return jsonify({"error": "Wallet already exists"}), 400

    passphrase = request.json.get("passphrase", "")

    if passphrase:
        passphrase_hash = hashlib.sha256(passphrase.encode()).hexdigest()
    else:
        passphrase_hash = None

    try:
        ordexcoind = rpc_manager.get_client("ordexcoind")
        ordexgoldd = rpc_manager.get_client("ordexgoldd")

        ordexcoin_address = ordexcoind.getnewaddress()
        ordexgold_address = ordexgoldd.getnewaddress()

        db.create_wallet(passphrase_hash)
        db.add_address(
            ordexcoin_address, "ordexcoin", "Default Receive", "default", False
        )
        db.add_address(
            ordexgold_address, "ordexgold", "Default Receive", "default", False
        )

        db.add_audit_log("INFO", "wallet", "New wallet created")

        return jsonify(
            {
                "success": True,
                "message": "Wallet created successfully",
                "wallet": {
                    "ordexcoin_address": ordexcoin_address,
                    "ordexgold_address": ordexgold_address,
                    "backup_passphrase_required": bool(passphrase),
                },
            }
        ), 201

    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        db.add_audit_log("ERROR", "wallet", f"Failed to create wallet: {str(e)}")
        return jsonify({"error": str(e)}), 500


@wallet_bp.route("/import", methods=["POST"])
def import_wallet():
    """Import an existing wallet from private key."""
    errors = validate_request(
        {"private_key": {"required": True, "type": "private_key", "format": "wif"}}
    )
    if errors:
        return jsonify({"errors": errors}), 400

    private_key = request.json.get("private_key")
    network = request.json.get("network", "ordexcoin")
    passphrase = request.json.get("passphrase", "")

    if passphrase:
        passphrase_hash = hashlib.sha256(passphrase.encode()).hexdigest()
    else:
        passphrase_hash = None

    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if db.has_wallet():
        return jsonify({"error": "Wallet already exists"}), 400

    try:
        rpc_client = rpc_manager.get_client(network)
        rpc_client.importprivkey(private_key, "imported", False)

        address = rpc_client.getnewaddress("imported")

        db.create_wallet(passphrase_hash)
        db.add_address(address, network, "Imported", "imported", False)

        db.add_audit_log("INFO", "wallet", f"Wallet imported on {network}")

        return jsonify(
            {
                "success": True,
                "message": "Wallet imported successfully",
                "wallet": {"address": address, "network": network},
            }
        ), 201

    except Exception as e:
        logger.error(f"Error importing wallet: {e}")
        db.add_audit_log("ERROR", "wallet", f"Failed to import wallet: {str(e)}")
        return jsonify({"error": str(e)}), 500


@wallet_bp.route("/info", methods=["GET"])
def get_wallet_info():
    """Get wallet information."""
    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        ordexcoind = rpc_manager.get_client("ordexcoind")
        ordexgoldd = rpc_manager.get_client("ordexgoldd")

        ordexcoin_balance = ordexcoind.getbalance()
        ordexgold_balance = ordexgoldd.getbalance()

        ordexcoin_addresses = db.get_addresses("ordexcoin", False)
        ordexgold_addresses = db.get_addresses("ordexgold", False)

        meta = db.get_wallet_meta()

        return jsonify(
            {
                "has_wallet": True,
                "ordexcoin": {
                    "balance": ordexcoin_balance,
                    "addresses": ordexcoin_addresses,
                },
                "ordexgold": {
                    "balance": ordexgold_balance,
                    "addresses": ordexgold_addresses,
                },
                "created_at": meta.get("created_at"),
                "last_backup": meta.get("last_backup"),
            }
        )

    except Exception as e:
        logger.error(f"Error getting wallet info: {e}")
        return jsonify({"error": str(e)}), 500


@wallet_bp.route("/sign-message", methods=["POST"])
def sign_message():
    """Sign a message with wallet address."""
    errors = validate_request(
        {
            "address": {"required": True, "type": "address"},
            "message": {"required": True, "type": "string"},
        }
    )
    if errors:
        return jsonify({"errors": errors}), 400

    address = request.json.get("address")
    message = request.json.get("message")
    network = request.json.get("network", "ordexcoin")

    rpc_manager = current_app.config["rpc_manager"]

    try:
        rpc_client = rpc_manager.get_client(network)
        signature = rpc_client.signmessage(address, message)

        return jsonify({"success": True, "signature": signature})

    except Exception as e:
        logger.error(f"Error signing message: {e}")
        return jsonify({"error": str(e)}), 500


@wallet_bp.route("/verify-message", methods=["POST"])
def verify_message():
    """Verify a signed message."""
    errors = validate_request(
        {
            "address": {"required": True, "type": "address"},
            "signature": {"required": True, "type": "string"},
            "message": {"required": True, "type": "string"},
        }
    )
    if errors:
        return jsonify({"errors": errors}), 400

    address = request.json.get("address")
    signature = request.json.get("signature")
    message = request.json.get("message")
    network = request.json.get("network", "ordexcoin")

    rpc_manager = current_app.config["rpc_manager"]

    try:
        rpc_client = rpc_manager.get_client(network)
        valid = rpc_client.verifymessage(address, signature, message)

        return jsonify({"valid": valid})

    except Exception as e:
        logger.error(f"Error verifying message: {e}")
        return jsonify({"error": str(e)}), 500


@wallet_bp.route("/backup", methods=["POST"])
def create_backup():
    """Create a wallet backup."""
    passphrase = request.json.get("passphrase", "")

    db = current_app.config["db_manager"].get_db()
    rpc_manager = current_app.config["rpc_manager"]

    if not db.has_wallet():
        return jsonify({"error": "No wallet found"}), 404

    try:
        meta = db.get_wallet_meta()
        if meta.get("backup_passphrase_hash") and not passphrase:
            return jsonify({"error": "Backup passphrase required"}), 400

        if passphrase:
            provided_hash = hashlib.sha256(passphrase.encode()).hexdigest()
            if provided_hash != meta.get("backup_passphrase_hash"):
                return jsonify({"error": "Invalid passphrase"}), 401

        from services.backup import BackupService

        backup_service = BackupService(current_app.config["DATA_DIR"])
        backup_path = backup_service.create_backup(passphrase)

        db.update_last_backup()
        db.add_audit_log("INFO", "wallet", "Wallet backup created")

        return jsonify({"success": True, "backup_path": backup_path})

    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({"error": str(e)}), 500


@wallet_bp.route("/restore", methods=["POST"])
def restore_backup():
    """Restore wallet from backup."""
    if "file" not in request.files:
        return jsonify({"error": "Backup file required"}), 400

    file = request.files["file"]
    passphrase = request.form.get("passphrase", "")

    db = current_app.config["db_manager"].get_db()

    try:
        from services.backup import BackupService

        backup_service = BackupService(current_app.config["DATA_DIR"])
        backup_service.restore_backup(file.read(), passphrase)

        db.add_audit_log("INFO", "wallet", "Wallet restored from backup")

        return jsonify({"success": True, "message": "Wallet restored successfully"})

    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return jsonify({"error": str(e)}), 500
