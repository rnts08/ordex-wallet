import os
import logging
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

from ordex_web_wallet.utils.logging_utils import (
    ensure_log_dir,
    get_logger,
    APP_LOG_FILE,
    log_app,
)
from ordex_web_wallet.config import config
from ordex_web_wallet.database import init_database

ensure_log_dir()
logger = get_logger("ordex_web_wallet", APP_LOG_FILE)

APP_VERSION = "1.0.1"


def validate_startup() -> tuple[bool, list[str]]:
    errors = []

    if config.validation_errors:
        return False, config.validation_errors

    try:
        from ordex_web_wallet.config import Config

        rt_errors = config.validate_runtime()
        errors.extend(rt_errors)
    except Exception as e:
        errors.append(f"Runtime validation failed: {str(e)}")

    return len(errors) == 0, errors


def create_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    CORS(app, supports_credentials=True)

    from ordex_web_wallet.api.auth import auth_bp
    from ordex_web_wallet.api.wallet import wallet_bp
    from ordex_web_wallet.api.admin import admin_bp
    from ordex_web_wallet.api import system_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(system_bp, url_prefix="/api/system")

    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

    @app.route("/api/info")
    def info():
        return jsonify(
            {"name": "Ordex Web Wallet", "version": APP_VERSION, "status": "running"}
        )

    @app.route("/")
    def index():
        return send_from_directory(frontend_path, "index.html")

    @app.route("/<path:filename>")
    def serve_static(filename):
        return send_from_directory(frontend_path, filename)

    return app


if __name__ == "__main__":
    valid, errors = validate_startup()
    if not valid:
        logger.critical(f"Startup validation failed: {errors}")
        print(f"ERROR: Startup validation failed: {errors}")
        exit(1)

    logger.info(f"Starting Ordex Web Wallet v{APP_VERSION}")
    log_app(logging.INFO, f"Application starting v{APP_VERSION}")

    init_database()
    app = create_app()

    valid, runtime_errors = validate_startup()
    if runtime_errors:
        logger.warning(f"Runtime issues detected: {runtime_errors}")
    else:
        logger.info("All services validated")

    app.run(host="0.0.0.0", port=5000)
