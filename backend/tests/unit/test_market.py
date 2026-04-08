"""
Unit tests for Market Service.
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from services.market import (
    MarketProvider,
    FallbackProvider,
    NestexProvider,
    get_market_provider,
)


class TestMarketProvider(unittest.TestCase):
    """Test cases for MarketProvider base class."""

    def test_get_prices_not_implemented(self):
        """Test that base class raises NotImplementedError."""
        provider = MarketProvider()

        with self.assertRaises(NotImplementedError):
            provider.get_prices()


class TestFallbackProvider(unittest.TestCase):
    """Test cases for FallbackProvider."""

    def test_get_prices_returns_placeholder(self):
        """Test fallback prices."""
        provider = FallbackProvider()
        prices = provider.get_prices()

        self.assertIn("ordexcoin", prices)
        self.assertIn("ordexgold", prices)
        self.assertEqual(prices["ordexcoin"]["symbol"], "OXC")
        self.assertEqual(prices["ordexgold"]["symbol"], "OXG")
        self.assertEqual(prices["ordexcoin"]["usd"], 0)
        self.assertEqual(prices["ordexgold"]["btc"], 0)


class TestNestexProvider(unittest.TestCase):
    """Test cases for NestexProvider."""

    def test_init_default(self):
        """Test NestexProvider initialization without API key."""
        provider = NestexProvider()
        self.assertIsNone(provider.api_key)

    def test_init_with_api_key(self):
        """Test NestexProvider initialization with API key."""
        provider = NestexProvider(api_key="test_key")
        self.assertEqual(provider.api_key, "test_key")

    def test_get_prices_fallback(self):
        """Test NestexProvider returns fallback prices."""
        provider = NestexProvider()
        prices = provider.get_prices()

        self.assertIn("ordexcoin", prices)
        self.assertIn("ordexgold", prices)
        self.assertEqual(prices["ordexcoin"]["usd"], 0)


class TestGetMarketProvider(unittest.TestCase):
    """Test cases for get_market_provider function."""

    def test_get_nestex_provider(self):
        """Test getting Nestex provider."""
        provider = get_market_provider("nestex")
        self.assertIsInstance(provider, NestexProvider)

    def test_get_fallback_provider(self):
        """Test getting Fallback provider."""
        provider = get_market_provider("fallback")
        self.assertIsInstance(provider, FallbackProvider)

    def test_get_unknown_provider_defaults_to_fallback(self):
        """Test unknown provider defaults to Fallback."""
        provider = get_market_provider("unknown")
        self.assertIsInstance(provider, FallbackProvider)

    def test_get_provider_case_insensitive(self):
        """Test provider lookup is case insensitive."""
        provider = get_market_provider("NESTEX")
        self.assertIsInstance(provider, NestexProvider)

    def test_get_provider_with_kwargs(self):
        """Test passing kwargs to provider."""
        provider = get_market_provider("nestex", api_key="my_key")
        self.assertEqual(provider.api_key, "my_key")


if __name__ == "__main__":
    unittest.main()
