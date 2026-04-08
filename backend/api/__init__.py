"""
API Module for OrdexWallet.

Contains all API blueprints and route handlers.
"""

import logging
import hashlib
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)


def register_blueprints(app):
    """Register all API blueprints."""
    from api.wallet import wallet_bp
    from api.assets import assets_bp
    from api.transactions import transactions_bp
    from api.system import system_bp
    from api.market import market_bp

    app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
    app.register_blueprint(assets_bp, url_prefix="/api/assets")
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(system_bp, url_prefix="/api/system")
    app.register_blueprint(market_bp, url_prefix="/api/market")
