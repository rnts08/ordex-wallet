"""
Unit tests for API Endpoints (wallet, assets, transactions, system, market).
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from flask import Flask


class TestWalletAPI(unittest.TestCase):
    """Test cases for Wallet API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["db_manager"] = Mock()
        self.app.config["rpc_manager"] = Mock()
        self.app.config["validation_service"] = Mock()
        self.app.config["DATA_DIR"] = "/tmp/test_data"

    def test_create_wallet_no_existing(self):
        """Test creating wallet when no wallet exists."""
        from api.wallet import create_wallet

        db_mock = Mock()
        db_mock.has_wallet.return_value = False

        rpc_mock = Mock()
        ordexcoind_mock = Mock()
        ordexcoind_mock.getnewaddress.return_value = "MtestOXC123"
        ordexgold_mock = Mock()
        ordexgold_mock.getnewaddress.return_value = "GtestOXG123"
        rpc_mock.get_client.side_effect = (
            lambda x: ordexcoind_mock if x == "ordexcoind" else ordexgold_mock
        )

        self.app.config["db_manager"].get_db.return_value = db_mock
        self.app.config["rpc_manager"] = rpc_mock

        with self.app.test_request_context(json={"passphrase": "test123"}):
            with patch("api.wallet.current_app", self.app):
                response = create_wallet()
                self.assertEqual(response[1], 201)

    def test_create_wallet_existing(self):
        """Test creating wallet when wallet already exists."""
        from api.wallet import create_wallet

        db_mock = Mock()
        db_mock.has_wallet.return_value = True

        self.app.config["db_manager"].get_db.return_value = db_mock

        with self.app.test_request_context(json={}):
            with patch("api.wallet.current_app", self.app):
                response = create_wallet()
                self.assertEqual(response[1], 400)
                self.assertIn("already exists", response[0].get_data(as_text=True))

    def test_get_wallet_info_no_wallet(self):
        """Test getting wallet info when no wallet exists."""
        from api.wallet import get_wallet_info

        db_mock = Mock()
        db_mock.has_wallet.return_value = False

        self.app.config["db_manager"].get_db.return_value = db_mock

        with self.app.test_request_context():
            with patch("api.wallet.current_app", self.app):
                response = get_wallet_info()
                self.assertEqual(response[1], 404)

    def test_get_wallet_info_with_wallet(self):
        """Test getting wallet info when wallet exists."""
        from api.wallet import get_wallet_info

        db_mock = Mock()
        db_mock.has_wallet.return_value = True
        db_mock.get_addresses.side_effect = lambda net, _: [
            {"address": f"Mtest{net}123"}
        ]
        db_mock.get_wallet_meta.return_value = {"created_at": "2026-01-01"}

        rpc_mock = Mock()
        ordexcoind_mock = Mock()
        ordexcoind_mock.getbalance.return_value = 10.5
        ordexgold_mock = Mock()
        ordexgold_mock.getbalance.return_value = 5.25
        rpc_mock.get_client.side_effect = (
            lambda x: ordexcoind_mock if x == "ordexcoind" else ordexgold_mock
        )

        self.app.config["db_manager"].get_db.return_value = db_mock
        self.app.config["rpc_manager"] = rpc_mock

        with self.app.test_request_context():
            with patch("api.wallet.current_app", self.app):
                response = get_wallet_info()
                self.assertEqual(response.status_code, 200)


class TestAssetsAPI(unittest.TestCase):
    """Test cases for Assets API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["db_manager"] = Mock()
        self.app.config["rpc_manager"] = Mock()

    def test_get_assets_no_wallet(self):
        """Test getting assets when no wallet exists."""
        from api.assets import get_assets

        db_mock = Mock()
        db_mock.has_wallet.return_value = False

        self.app.config["db_manager"].get_db.return_value = db_mock

        with self.app.test_request_context():
            with patch("api.assets.current_app", self.app):
                response = get_assets()
                self.assertEqual(response[1], 404)

    def test_get_assets_with_wallet(self):
        """Test getting assets when wallet exists."""
        from api.assets import get_assets

        db_mock = Mock()
        db_mock.has_wallet.return_value = True

        rpc_mock = Mock()
        ordexcoind_mock = Mock()
        ordexcoind_mock.getbalance.return_value = 100.0
        ordexcoind_mock.get_sync_status.return_value = {
            "connected": True,
            "blocks": 1000,
        }
        ordexgold_mock = Mock()
        ordexgold_mock.getbalance.return_value = 50.0
        ordexgold_mock.get_sync_status.return_value = {"connected": True, "blocks": 500}
        rpc_mock.get_client.side_effect = (
            lambda x: ordexcoind_mock if x == "ordexcoind" else ordexgold_mock
        )

        self.app.config["db_manager"].get_db.return_value = db_mock
        self.app.config["rpc_manager"] = rpc_mock

        with self.app.test_request_context():
            with patch("api.assets.current_app", self.app):
                response = get_assets()
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.get_data(as_text=True))
                self.assertIn("ordexcoin", data)
                self.assertIn("ordexgold", data)

    def test_get_asset_invalid(self):
        """Test getting invalid asset."""
        from api.assets import get_asset

        with self.app.test_request_context():
            with patch("api.assets.current_app", self.app):
                response = get_asset("invalid")
                self.assertEqual(response[1], 400)


class TestTransactionsAPI(unittest.TestCase):
    """Test cases for Transactions API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["db_manager"] = Mock()
        self.app.config["rpc_manager"] = Mock()
        self.app.config["validation_service"] = Mock()

    def test_get_transactions_no_wallet(self):
        """Test getting transactions when no wallet exists."""
        from api.transactions import get_transactions

        db_mock = Mock()
        db_mock.has_wallet.return_value = False

        self.app.config["db_manager"].get_db.return_value = db_mock

        with self.app.test_request_context():
            with patch("api.transactions.current_app", self.app):
                response = get_transactions()
                self.assertEqual(response[1], 404)

    def test_get_transactions_with_wallet(self):
        """Test getting transactions when wallet exists."""
        from api.transactions import get_transactions

        db_mock = Mock()
        db_mock.has_wallet.return_value = True
        db_mock.get_transactions.return_value = [
            {"txid": "tx1", "amount": 1.0, "confirmations": 6}
        ]

        self.app.config["db_manager"].get_db.return_value = db_mock

        with self.app.test_request_context():
            with patch("api.transactions.current_app", self.app):
                response = get_transactions()
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.get_data(as_text=True))
                self.assertEqual(len(data["transactions"]), 1)

    def test_send_transaction_insufficient_funds(self):
        """Test sending transaction with insufficient funds."""
        from api.transactions import send_transaction

        db_mock = Mock()
        db_mock.has_wallet.return_value = True

        rpc_mock = Mock()
        rpc_client_mock = Mock()
        rpc_client_mock.listunspent.return_value = []
        rpc_mock.get_client.return_value = rpc_client_mock

        validation_mock = Mock()
        validation_mock.validate_address.return_value = Mock(valid=True)
        validation_mock.validate_amount.return_value = Mock(valid=True)

        self.app.config["db_manager"].get_db.return_value = db_mock
        self.app.config["rpc_manager"] = rpc_mock
        self.app.config["validation_service"] = validation_mock

        with self.app.test_request_context(json={"address": "Mtest", "amount": "1.0"}):
            with patch("api.transactions.current_app", self.app):
                response = send_transaction()
                self.assertEqual(response[1], 400)
                self.assertIn("No unspent", response[0].get_data(as_text=True))


class TestSystemAPI(unittest.TestCase):
    """Test cases for System API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["db_manager"] = Mock()
        self.app.config["rpc_manager"] = Mock()
        self.app.config["config_generator"] = Mock()
        self.app.config["validation_service"] = Mock()

    def test_health_check_healthy(self):
        """Test health check when all connected."""
        from api.system import health_check

        rpc_mock = Mock()
        rpc_mock.get_sync_status.return_value = {
            "ordexcoind": {
                "connected": True,
                "blocks": 1000,
                "headers": 1000,
                "syncing": False,
            },
            "ordexgoldd": {
                "connected": True,
                "blocks": 500,
                "headers": 500,
                "syncing": False,
            },
        }

        db_mock = Mock()
        db_mock.has_wallet.return_value = True

        self.app.config["rpc_manager"] = rpc_mock
        self.app.config["db_manager"].get_db.return_value = db_mock
        self.app.config["config_generator"] = Mock()

        with self.app.test_request_context():
            with patch("api.system.current_app", self.app):
                with patch("os.times", return_value=Mock(real=1234567890.0)):
                    response = health_check()
                    if isinstance(response, tuple):
                        self.assertEqual(response[1], 200)
                        data = json.loads(response[0].get_data(as_text=True))
                    else:
                        self.assertEqual(response.status_code, 200)
                        data = json.loads(response.get_data(as_text=True))
                    self.assertEqual(data["status"], "healthy")
                    self.assertIn("sync", data)
                    self.assertEqual(data["sync"]["ordexcoind"]["percentage"], 100.0)
                    self.assertEqual(data["sync"]["ordexgoldd"]["percentage"], 100.0)

    def test_health_check_syncing(self):
        """Test health check when daemons are syncing."""
        from api.system import health_check

        rpc_mock = Mock()
        rpc_mock.get_sync_status.return_value = {
            "ordexcoind": {
                "connected": True,
                "blocks": 500,
                "headers": 1000,
                "syncing": True,
            },
            "ordexgoldd": {
                "connected": True,
                "blocks": 250,
                "headers": 500,
                "syncing": True,
            },
        }

        db_mock = Mock()
        db_mock.has_wallet.return_value = True

        self.app.config["rpc_manager"] = rpc_mock
        self.app.config["db_manager"].get_db.return_value = db_mock
        self.app.config["config_generator"] = Mock()

        with self.app.test_request_context():
            with patch("api.system.current_app", self.app):
                response = health_check()
                if isinstance(response, tuple):
                    data = json.loads(response[0].get_data(as_text=True))
                else:
                    data = json.loads(response.get_data(as_text=True))
                self.assertEqual(data["status"], "healthy")
                self.assertEqual(data["sync"]["ordexcoind"]["percentage"], 50.0)
                self.assertEqual(data["sync"]["ordexgoldd"]["percentage"], 50.0)
                self.assertTrue(data["sync"]["ordexcoind"]["syncing"])
                self.assertTrue(data["sync"]["ordexgoldd"]["syncing"])

    def test_health_check_starting(self):
        """Test health check when app is still starting."""
        from api.system import health_check

        self.app.config["rpc_manager"] = None
        self.app.config["db_manager"] = None

        with self.app.test_request_context():
            with patch("api.system.current_app", self.app):
                response = health_check()
                if isinstance(response, tuple):
                    self.assertEqual(response[1], 503)
                    data = json.loads(response[0].get_data(as_text=True))
                else:
                    self.assertEqual(response.status_code, 503)
                    data = json.loads(response.get_data(as_text=True))
                self.assertEqual(data["status"], "starting")
                self.assertIn("message", data)

    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        from api.system import metrics
        from prometheus_client import CONTENT_TYPE_LATEST

        rpc_mock = Mock()
        rpc_mock.ordexcoind.getbalance.return_value = 100.5
        rpc_mock.ordexgoldd.getbalance.return_value = 50.25
        rpc_mock.get_sync_status.return_value = {
            "ordexcoind": {"blocks": 1000, "headers": 1000},
            "ordexgoldd": {"blocks": 500, "headers": 500},
        }

        self.app.config["rpc_manager"] = rpc_mock
        self.app.config["config_generator"] = Mock()

        with self.app.test_request_context():
            with patch("api.system.current_app", self.app):
                response = metrics()
                self.assertEqual(response[1], 200)
                self.assertEqual(response[2]["Content-Type"], CONTENT_TYPE_LATEST)
                self.assertIn(b"ordexwallet_balance", response[0])

    def test_health_check_unhealthy(self):
        """Test health check when not connected."""
        from api.system import health_check

        rpc_mock = Mock()
        rpc_mock.get_sync_status.side_effect = Exception("Connection failed")

        self.app.config["rpc_manager"] = rpc_mock

        with self.app.test_request_context():
            with patch("api.system.current_app", self.app):
                response = health_check()
                if isinstance(response, tuple):
                    self.assertEqual(response[1], 500)
                    data = json.loads(response[0].get_data(as_text=True))
                else:
                    self.assertEqual(response.status_code, 500)
                    data = json.loads(response.get_data(as_text=True))
                self.assertEqual(data["status"], "unhealthy")

    def test_get_daemon_config(self):
        """Test getting daemon config."""
        from api.system import get_daemon_config

        config_gen_mock = Mock()
        config_gen_mock.get_daemon_config.side_effect = lambda x: {
            "rpcport": 25173 if x == "ordexcoind" else 25466
        }

        self.app.config["config_generator"] = config_gen_mock

        with self.app.test_request_context():
            with patch("api.system.current_app", self.app):
                response = get_daemon_config()
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.get_data(as_text=True))
                self.assertIn("ordexcoind", data)

    def test_update_daemon_config_invalid_daemon(self):
        """Test updating config with invalid daemon."""
        from api.system import update_daemon_config

        with self.app.test_request_context(json={"daemon": "invalid", "config": {}}):
            with patch("api.system.current_app", self.app):
                response = update_daemon_config()
                self.assertEqual(response[1], 400)


class TestMarketAPI(unittest.TestCase):
    """Test cases for Market API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["app_config"] = {
            "market": {"enabled": True, "default_exchange": "fallback"}
        }

    def test_get_prices_fallback(self):
        """Test getting prices in fallback mode."""
        from api.market import get_prices

        with self.app.test_request_context():
            with patch("api.market.current_app", self.app):
                response = get_prices()
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.get_data(as_text=True))
                self.assertTrue(data["fallback_mode"])

    def test_get_news_fallback(self):
        """Test getting news in fallback mode."""
        from api.market import get_news

        with self.app.test_request_context():
            with patch("api.market.current_app", self.app):
                response = get_news()
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.get_data(as_text=True))
                self.assertTrue(data["fallback_mode"])

    def test_get_price_history_invalid_asset(self):
        """Test getting price history for invalid asset."""
        from api.market import get_price_history

        with self.app.test_request_context():
            with patch("api.market.current_app", self.app):
                response = get_price_history("invalid")
                self.assertEqual(response[1], 400)

    def test_get_news_fallback(self):
        """Test getting news in fallback mode."""
        from api.market import get_news

        with self.app.test_request_context():
            with patch("api.market.current_app", self.app):
                response = get_news()
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.get_data(as_text=True))
                self.assertTrue(data["fallback_mode"])


if __name__ == "__main__":
    unittest.main()
