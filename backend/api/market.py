"""
Market API Blueprint.

Handles market data with pluggable providers and fallback mode.
"""

import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

market_bp = Blueprint("market", __name__)


@market_bp.route("/prices", methods=["GET"])
def get_prices():
    """Get current prices (fallback mode - mock data)."""
    config = current_app.config["app_config"]
    market_config = config.get("market", {})

    if not market_config.get("enabled", True):
        return jsonify(
            {"prices": {}, "fallback_mode": True, "message": "Market data disabled"}
        )

    try:
        prices = _fetch_prices(market_config)

        return jsonify({"prices": prices, "fallback_mode": True, "source": "fallback"})

    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        return jsonify(
            {"prices": _get_fallback_prices(), "fallback_mode": True, "error": str(e)}
        )


@market_bp.route("/history/<asset>", methods=["GET"])
def get_price_history(asset):
    """Get price history for asset (fallback mode)."""
    if asset not in ["ordexcoin", "ordexgold"]:
        return jsonify({"error": "Invalid asset"}), 400

    return jsonify(
        {
            "asset": asset,
            "history": [],
            "fallback_mode": True,
            "message": "Price history not available in fallback mode",
        }
    )


@market_bp.route("/news", methods=["GET"])
def get_news():
    """Get news (fallback mode - mock data)."""
    config = current_app.config["app_config"]
    market_config = config.get("market", {})

    if not market_config.get("enabled", True):
        return jsonify({"news": [], "fallback_mode": True})

    return jsonify({"news": _get_fallback_news(), "fallback_mode": True})


def _fetch_prices(market_config):
    """Fetch prices from configured provider."""
    provider = market_config.get("default_exchange", "nestex")

    try:
        from services.market import get_market_provider

        provider_instance = get_market_provider(provider)
        return provider_instance.get_prices()
    except Exception as e:
        logger.warning(f"Market provider {provider} failed: {e}")
        return _get_fallback_prices()


def _get_fallback_prices():
    """Return fallback/mock prices."""
    return {
        "ordexcoin": {"symbol": "OXC", "usd": 0.0, "btc": 0.0, "last_update": None},
        "ordexgold": {"symbol": "OXG", "usd": 0.0, "btc": 0.0, "last_update": None},
    }


def _get_fallback_news():
    """Return fallback news items."""
    return [
        {
            "title": "OrdexNetwork Wallet",
            "description": "Welcome to your new OrdexWallet",
            "url": "https://ordexnetwork.org",
            "date": None,
        }
    ]
