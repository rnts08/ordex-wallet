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

    try:
        config_generator = ConfigGenerator(config_dir, data_dir)

        if config_generator.is_first_startup():
            logger.info("First startup - generating configuration...")
            config_generator.generate_all_configs()
        else:
            logger.info("Configuration already exists, loading...")

        app.config["config_generator"] = config_generator
        app.config["app_config"] = config_generator.load_config()
    except Exception as e:
        logger.error(f"Could not initialize config: {e}")
        app.config["config_generator"] = None
        app.config["app_config"] = None
        logger.error(
            "App cannot start without valid config. Please check daemon configuration."
        )

    try:
        db_manager = DatabaseManager(data_dir)
        logger.info("DatabaseManager initialized successfully")
        app.config["db_manager"] = db_manager
    except Exception as e:
        logger.warning(f"Could not initialize database: {e}")
        app.config["db_manager"] = None

    try:
        rpc_manager = RPCClientManager(app.config["app_config"])

        try:
            for client in [rpc_manager.ordexcoind, rpc_manager.ordexgoldd]:
                try:
                    wallets = client.listwallets()
                    if "wallet" not in wallets:
                        try:
                            client.call("createwallet", "wallet")
                            logger.info(f"Created new wallet for {client.daemon_name}")
                        except Exception as e:
                            if "Database already exists" in str(e):
                                logger.info(
                                    f"Wallet already exists for {client.daemon_name}, loading..."
                                )
                            else:
                                raise
                    client.loadwallet("wallet")
                    logger.info(f"Loaded wallet for {client.daemon_name}")
                except Exception as e:
                    logger.warning(f"Wallet init error for {client.daemon_name}: {e}")
        except Exception as e:
            logger.warning(f"Could not initialize wallet: {e}")

        app.config["rpc_manager"] = rpc_manager
    except Exception as e:
        logger.warning(f"Could not initialize RPC manager: {e}")
        app.config["rpc_manager"] = None

    app.config["validation_service"] = ValidationService()

    from api import register_blueprints

    register_blueprints(app)

    @app.route("/")
    def serve_index():
        """Serve the frontend index."""
        try:
            from pathlib import Path

            frontend_path = Path("/frontend/index.html")
            if not frontend_path.exists():
                frontend_path = Path(__file__).parent / "frontend" / "index.html"
            return frontend_path.read_text(), 200, {"Content-Type": "text/html"}
        except Exception as e:
            logger.error(f"Error serving index: {e}")
            return jsonify({"error": "Frontend not found"}), 404

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        """Serve JavaScript files."""
        try:
            from pathlib import Path

            js_path = Path("/frontend/js") / filename
            if not js_path.exists():
                js_path = Path(__file__).parent / "frontend" / "js" / filename
            if not js_path.exists():
                return jsonify({"error": "Not found"}), 404
            return js_path.read_text(), 200, {"Content-Type": "application/javascript"}
        except Exception as e:
            logger.error(f"Error serving JS: {e}")
            return jsonify({"error": "Not found"}), 404

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        """Serve CSS files."""
        try:
            from pathlib import Path

            css_path = Path("/frontend/css") / filename
            if not css_path.exists():
                css_path = Path(__file__).parent / "frontend" / "css" / filename
            if not css_path.exists():
                return jsonify({"error": "Not found"}), 404
            return css_path.read_text(), 200, {"Content-Type": "text/css"}
        except Exception as e:
            logger.error(f"Error serving CSS: {e}")
            return jsonify({"error": "Not found"}), 404

    @app.route("/<path:filename>")
    def serve_static_files(filename):
        """Serve static files (images, etc)."""
        if (
            filename.startswith("api/")
            or filename.startswith("js/")
            or filename.startswith("css/")
        ):
            return jsonify({"error": "Not found"}), 404
        try:
            from pathlib import Path

            file_path = Path("/frontend") / filename
            if not file_path.exists():
                file_path = Path(__file__).parent / "frontend" / filename

            if not file_path.exists():
                return jsonify({"error": "Not found"}), 404

            content_type = "image/png"
            if filename.endswith(".svg"):
                content_type = "image/svg+xml"
            elif filename.endswith(".ico"):
                content_type = "image/x-icon"

            return file_path.read_bytes(), 200, {"Content-Type": content_type}
        except Exception as e:
            logger.error(f"Error serving static file: {e}")
            return jsonify({"error": "Not found"}), 404

    # Serve frontend for all non-API routes (must be after API blueprints)
    @app.route("/<path:non_api>")
    def serve_frontend(non_api):
        """Serve the frontend HTML for non-API routes."""
        if non_api.startswith("api/"):
            return jsonify({"error": "Not found"}), 404
        try:
            from pathlib import Path

            # Frontend is copied to /frontend in the container
            frontend_path = Path("/frontend/index.html")
            if not frontend_path.exists():
                # Fallback: try relative to current directory
                frontend_path = Path(__file__).parent / "frontend" / "index.html"
            return frontend_path.read_text(), 200, {"Content-Type": "text/html"}
        except Exception as e:
            logger.error(f"Error serving frontend: {e}")
            return jsonify({"error": "Frontend not found"}), 404

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
    config_dir = os.environ.get("CONFIG_DIR", "/data/config")
    data_dir = os.environ.get("DATA_DIR", "/data")
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"

    app = create_app(config_dir, data_dir)
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
