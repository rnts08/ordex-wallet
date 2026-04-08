"""
Flask API Application for OrdexWallet.

REST API for wallet management, transactions, and system operations.
"""

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import ConfigGenerator
from database import DatabaseManager
from rpc import RPCClientManager
from validation import ValidationService, ValidationResult

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app(config_dir: str = None, data_dir: str = None) -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)

    if config_dir is None:
        config_dir = os.environ.get("CONFIG_DIR", "/config")
    if data_dir is None:
        data_dir = os.environ.get("DATA_DIR", "/data")

    app.config["CONFIG_DIR"] = config_dir
    app.config["DATA_DIR"] = data_dir
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

    CORS(app)

    config_generator = ConfigGenerator(config_dir, data_dir)

    if config_generator.is_first_startup():
        logger.info("First startup - generating configuration...")
        config_generator.generate_all_configs()

    app.config["config_generator"] = config_generator
    app.config["app_config"] = config_generator.load_config()

    db_manager = DatabaseManager(data_dir)
    app.config["db_manager"] = db_manager

    rpc_manager = RPCClientManager(app.config["app_config"])
    app.config["rpc_manager"] = rpc_manager

    app.config["validation_service"] = ValidationService()

    from api import register_blueprints

    register_blueprints(app)

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    return app


def main():
    """Run the Flask application."""
    config_dir = os.environ.get("CONFIG_DIR", "./config")
    data_dir = os.environ.get("DATA_DIR", "./data")
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"

    app = create_app(config_dir, data_dir)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
