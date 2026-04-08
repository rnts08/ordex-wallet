"""
Market Service for OrdexWallet.

Pluggable market data providers.
"""

import logging

logger = logging.getLogger(__name__)


class MarketProvider:
    """Base class for market data providers."""

    def get_prices(self):
        """Get current prices."""
        raise NotImplementedError


class FallbackProvider(MarketProvider):
    """Fallback provider when no exchange is available."""

    def get_prices(self):
        """Return placeholder prices."""
        return {
            "ordexcoin": {"symbol": "OXC", "usd": 0, "btc": 0},
            "ordexgold": {"symbol": "OXG", "usd": 0, "btc": 0},
        }


class NestexProvider(MarketProvider):
    """Nestex exchange provider (placeholder)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def get_prices(self):
        logger.warning("Nestex provider not implemented, using fallback")
        return FallbackProvider().get_prices()


def get_market_provider(name: str, **kwargs) -> MarketProvider:
    """Get market data provider by name."""
    providers = {"nestex": NestexProvider, "fallback": FallbackProvider}

    provider_class = providers.get(name.lower(), FallbackProvider)
    return provider_class(**kwargs)
