import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from ordex_web_wallet.config import config
from ordex_web_wallet.database import init_database


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

    @app.route("/")
    def index():
        return send_from_directory(frontend_path, "index.html")

    @app.route("/<path:filename>")
    def serve_static(filename):
        return send_from_directory(frontend_path, filename)

    return app


if __name__ == "__main__":
    init_database()
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
