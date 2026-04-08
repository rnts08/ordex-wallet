"""
Unit tests for RPC Client Service.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from rpc import (
    OrdexRPCClient,
    OrdexCoinClient,
    OrdexGoldClient,
    RPCClientManager,
    RPCError,
    RPCConnectionError,
)


class TestOrdexRPCClient(unittest.TestCase):
    """Test cases for OrdexRPCClient class."""

    def test_init_defaults(self):
        """Test client initialization with defaults."""
        client = OrdexRPCClient()

        self.assertEqual(client.host, "localhost")
        self.assertEqual(client.port, 25173)
        self.assertEqual(client.timeout, 30)
        self.assertEqual(client.daemon_name, "ordexcoind")
        self.assertEqual(client.url, "http://localhost:25173")

    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = OrdexRPCClient(
            host="192.168.1.1",
            port=9999,
            user="testuser",
            password="testpass",
            timeout=60,
            daemon_name="ordexgoldd",
        )

        self.assertEqual(client.host, "192.168.1.1")
        self.assertEqual(client.port, 9999)
        self.assertEqual(client.user, "testuser")
        self.assertEqual(client.password, "testpass")
        self.assertEqual(client.timeout, 60)
        self.assertEqual(client.daemon_name, "ordexgoldd")

    def test_build_auth_with_credentials(self):
        """Test auth building with credentials."""
        client = OrdexRPCClient()
        client.user = "user"
        client.password = "pass"
        auth = client._build_auth()

        self.assertEqual(auth, ("user", "pass"))

    def test_build_auth_without_credentials(self):
        """Test auth building without credentials."""
        client = OrdexRPCClient()
        auth = client._build_auth()

        self.assertIsNone(auth)

    def test_call_success(self):
        """Test successful RPC call."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"blocks": 100}, "error": None}
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        result = client.call("getinfo")

        self.assertEqual(result, {"blocks": 100})

        client.session.post.assert_called_once()
        call_args = client.session.post.call_args
        self.assertEqual(call_args.kwargs["json"]["method"], "getinfo")

    def test_call_with_args(self):
        """Test RPC call with arguments."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "address123", "error": None}
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        result = client.call("getnewaddress", "account", "p2pkh")

        self.assertEqual(result, "address123")

        call_args = client.session.post.call_args
        self.assertEqual(call_args.kwargs["json"]["params"], ["account", "p2pkh"])

    def test_call_rpc_error(self):
        """Test RPC error handling."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": None,
            "error": {"code": -32602, "message": "Invalid params"},
        }
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        with self.assertRaises(RPCError) as ctx:
            client.call("getnewaddress")

        self.assertEqual(ctx.exception.code, -32602)
        self.assertEqual(ctx.exception.message, "Invalid params")

    def test_call_connection_error(self):
        """Test connection error handling."""
        import requests

        client = OrdexRPCClient()

        client.session = MagicMock()
        client.session.post.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        with self.assertRaises(RPCConnectionError) as ctx:
            client.call("getinfo")

        self.assertIn("Connection failed", str(ctx.exception))

    def test_call_timeout(self):
        """Test timeout handling."""
        import requests

        client = OrdexRPCClient()

        client.session = MagicMock()
        client.session.post.side_effect = requests.exceptions.Timeout(
            "Request timed out"
        )

        with self.assertRaises(RPCConnectionError) as ctx:
            client.call("getinfo")

        self.assertIn("timed out", str(ctx.exception))

    def test_getinfo(self):
        """Test getinfo method."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"blocks": 100, "difficulty": 1000.0},
            "error": None,
        }
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        result = client.getinfo()

        self.assertEqual(result["blocks"], 100)
        self.assertEqual(result["difficulty"], 1000.0)

    def test_getbalance(self):
        """Test getbalance method."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": 10.5, "error": None}
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        result = client.getbalance()
        self.assertEqual(result, 10.5)

        result = client.getbalance("account", 6)

        call_args = client.session.post.call_args
        self.assertEqual(call_args.kwargs["json"]["params"], ["account", 6])

    def test_getnewaddress(self):
        """Test getnewaddress method."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "M1234567890abcdef", "error": None}
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        result = client.getnewaddress("testaccount")

        self.assertEqual(result, "M1234567890abcdef")

    def test_listtransactions(self):
        """Test listtransactions method."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        tx_list = [{"txid": "tx1", "amount": 1.0}, {"txid": "tx2", "amount": -0.5}]
        mock_response.json.return_value = {"result": tx_list, "error": None}
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        result = client.listtransactions("account", 10, 0)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["txid"], "tx1")

    def test_listunspent(self):
        """Test listunspent method."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        utxo = [{"txid": "tx1", "vout": 0, "amount": 1.0, "confirmations": 6}]
        mock_response.json.return_value = {"result": utxo, "error": None}
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        result = client.listunspent(1, 999999, ["address1"])

        call_args = client.session.post.call_args
        self.assertEqual(call_args.kwargs["json"]["params"], [1, 999999, ["address1"]])

    def test_is_connected(self):
        """Test is_connected method."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": None, "error": None}
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        self.assertTrue(client.is_connected())

        import requests

        client.session.post.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )
        self.assertFalse(client.is_connected())

    def test_get_sync_status_connected(self):
        """Test get_sync_status when connected."""
        client = OrdexRPCClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"blocks": 100, "headers": 200, "verificationprogress": 0.5},
            "error": None,
        }
        mock_response.raise_for_status = MagicMock()

        client.session = MagicMock()
        client.session.post.return_value = mock_response

        status = client.get_sync_status()

        self.assertTrue(status["connected"])
        self.assertEqual(status["blocks"], 100)
        self.assertTrue(status["syncing"])

    def test_get_sync_status_disconnected(self):
        """Test get_sync_status when disconnected."""
        client = OrdexRPCClient()

        import requests

        client.session = MagicMock()
        client.session.post.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        status = client.get_sync_status()

        self.assertFalse(status["connected"])
        self.assertIn("error", status)


class TestOrdexCoinClient(unittest.TestCase):
    """Test OrdexCoinClient specialization."""

    def test_default_port(self):
        """Test default port for ordexcoind."""
        client = OrdexCoinClient()
        self.assertEqual(client.port, 25173)
        self.assertEqual(client.daemon_name, "ordexcoind")


class TestOrdexGoldClient(unittest.TestCase):
    """Test OrdexGoldClient specialization."""

    def test_default_port(self):
        """Test default port for ordexgoldd."""
        client = OrdexGoldClient()
        self.assertEqual(client.port, 25466)
        self.assertEqual(client.daemon_name, "ordexgoldd")


class TestRPCClientManager(unittest.TestCase):
    """Test RPCClientManager class."""

    def test_init(self):
        """Test manager initialization."""
        config = {
            "daemons": {
                "ordexcoind": {
                    "host": "localhost",
                    "port": 25173,
                    "username": "user1",
                    "password": "pass1",
                },
                "ordexgoldd": {
                    "host": "localhost",
                    "port": 25466,
                    "username": "user2",
                    "password": "pass2",
                },
            }
        }

        manager = RPCClientManager(config)

        self.assertIsInstance(manager.ordexcoind, OrdexCoinClient)
        self.assertIsInstance(manager.ordexgoldd, OrdexGoldClient)

    def test_get_client(self):
        """Test get_client method."""
        config = {
            "daemons": {
                "ordexcoind": {
                    "host": "localhost",
                    "port": 25173,
                    "username": "u",
                    "password": "p",
                },
                "ordexgoldd": {
                    "host": "localhost",
                    "port": 25466,
                    "username": "u",
                    "password": "p",
                },
            }
        }

        manager = RPCClientManager(config)

        client = manager.get_client("ordexcoind")
        self.assertIsInstance(client, OrdexCoinClient)

        client = manager.get_client("ordexgoldd")
        self.assertIsInstance(client, OrdexGoldClient)

        with self.assertRaises(ValueError):
            manager.get_client("unknown")

    def test_get_client_invalid(self):
        """Test get_client with invalid daemon name."""
        config = {
            "daemons": {
                "ordexcoind": {
                    "host": "localhost",
                    "port": 25173,
                    "username": "u",
                    "password": "p",
                },
                "ordexgoldd": {
                    "host": "localhost",
                    "port": 25466,
                    "username": "u",
                    "password": "p",
                },
            }
        }

        manager = RPCClientManager(config)

        with self.assertRaises(ValueError):
            manager.get_client("invalid_daemon")


if __name__ == "__main__":
    unittest.main()
