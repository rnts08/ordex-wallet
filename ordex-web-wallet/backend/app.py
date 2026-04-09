import os
from flask import Flask, jsonify
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

    @app.route("/")
    def index():
        return jsonify(
            {
                "name": "Ordex Web Wallet",
                "version": "1.0.0",
                "status": "running",
            }
        )

    return app


if __name__ == "__main__":
    init_database()
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
