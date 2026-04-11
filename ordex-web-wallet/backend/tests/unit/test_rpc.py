import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestDaemonManager:
    """Test DaemonManager RPC functionality."""

    @patch("ordex_web_wallet.rpc.requests.Session")
    def test_get_url_with_wallet(self, mock_session):
        from ordex_web_wallet.rpc import DaemonManager

        dm = DaemonManager("ordex", "password")

        oxc_url = dm._get_url("ordexcoin")
        oxg_url = dm._get_url("ordexgold")

        assert "ordexcoind" in oxc_url
        assert "ordexgoldd" in oxg_url
        assert "5332" in oxc_url
        assert "5333" in oxg_url

    @patch("ordex_web_wallet.rpc.requests.Session")
    def test_get_url_with_wallet_name(self, mock_session):
        from ordex_web_wallet.rpc import DaemonManager

        dm = DaemonManager("ordex", "password")

        url = dm._get_url("ordexcoin", "wallet_1_ordexcoin")

        assert "wallet_1_ordexcoin" in url

    @patch("ordex_web_wallet.rpc.requests.Session")
    def test_is_wallet_loaded_true(self, mock_session):
        from ordex_web_wallet.rpc import DaemonManager

        dm = DaemonManager("ordex", "password")
        dm._call = MagicMock(return_value=["wallet_1_ordexcoin", "wallet_2_ordexcoin"])

        result = dm.is_wallet_loaded("ordexcoin", "wallet_1_ordexcoin")

        assert result is True

    @patch("ordex_web_wallet.rpc.requests.Session")
    def test_is_wallet_loaded_false(self, mock_session):
        from ordex_web_wallet.rpc import DaemonManager

        dm = DaemonManager("ordex", "password")
        dm._call = MagicMock(return_value=[])

        result = dm.is_wallet_loaded("ordexcoin", "wallet_1_ordexcoin")

        assert result is False

    @patch("ordex_web_wallet.rpc.requests.Session")
    def test_load_wallet_success(self, mock_session):
        from ordex_web_wallet.rpc import DaemonManager, RPCError

        dm = DaemonManager("ordex", "password")
        dm._call = MagicMock(return_value=True)

        dm.load_wallet("ordexcoin", "wallet_1_ordexcoin")

        dm._call.assert_called_once()

    @patch("ordex_web_wallet.rpc.requests.Session")
    def test_load_wallet_already_loaded(self, mock_session):
        from ordex_web_wallet.rpc import DaemonManager, RPCError

        dm = DaemonManager("ordex", "password")
        dm._call = MagicMock(side_effect=RPCError(-1, "Wallet already loaded"))

        try:
            dm.load_wallet("ordexcoin", "wallet_1_ordexcoin")
        except RPCError:
            pytest.fail("Should have handled 'already loaded' error")

    @patch("ordex_web_wallet.rpc.requests.Session")
    def test_create_user_wallet(self, mock_session):
        from ordex_web_wallet.rpc import DaemonManager

        dm = DaemonManager("ordex", "password")
        dm._call = MagicMock(return_value=True)

        wallet_name = dm.create_user_wallet(1, "ordexcoin", "passphrase123")

        assert wallet_name == "wallet_1_ordexcoin"
        dm._call.assert_called_once()

    @patch("ordex_web_wallet.rpc.requests.Session")
    def test_get_user_balance(self, mock_session):
        from ordex_web_wallet.rpc import DaemonManager

        dm = DaemonManager("ordex", "password")
        dm._call = MagicMock(return_value=100.5)

        balance = dm.get_user_balance(1, "ordexcoin")

        assert balance == 100.5
        assert isinstance(balance, float)


class TestRPCError:
    """Test RPCError class."""

    def test_rpc_error_attributes(self):
        from ordex_web_wallet.rpc import RPCError

        error = RPCError(-32600, "Invalid method")

        assert error.code == -32600
        assert error.message == "Invalid method"
        assert "Invalid method" in str(error)

    def test_sanitize_rpc_error_connection(self):
        from ordex_web_wallet.rpc import sanitize_rpc_error, RPCError

        error = RPCError(-1, "Connection refused")

        result = sanitize_rpc_error(error)

        assert "Cannot connect" in result
        assert "Connection refused" not in result

    def test_sanitize_rpc_error_insufficient_funds(self):
        from ordex_web_wallet.rpc import sanitize_rpc_error, RPCError

        error = RPCError(-4, "Insufficient funds")

        result = sanitize_rpc_error(error)

        assert "Insufficient funds" in result

    def test_sanitize_rpc_error_invalid_address(self):
        from ordex_web_wallet.rpc import sanitize_rpc_error, RPCError

        error = RPCError(-5, "Invalid address")

        result = sanitize_rpc_error(error)

        assert "address is invalid" in result
        assert "Invalid address" not in result

    def test_sanitize_rpc_error_wallet_not_found(self):
        from ordex_web_wallet.rpc import sanitize_rpc_error, RPCError

        error = RPCError(-18, "Wallet not found")

        result = sanitize_rpc_error(error)

        assert "not found" in result.lower()

    def test_sanitize_rpc_error_invalid_rpc_handle(self):
        from ordex_web_wallet.rpc import sanitize_rpc_error, RPCError

        error = RPCError(-1, "Invalid RPC handle")

        result = sanitize_rpc_error(error)

        assert "Wallet not loaded" in result


class TestRPCContext:
    """Test HTTPRPCContext for direct daemon calls."""

    def test_http_rpc_context_init(self):
        from ordex_web_wallet.rpc import HTTPRPCContext

        ctx = HTTPRPCContext(
            "ordexcoin", "wallet_1_ordexcoin", "ordex", "password", 5332, "localhost"
        )

        assert ctx.chain == "ordexcoin"
        assert ctx.wallet_name == "wallet_1_ordexcoin"
        assert ctx.rpc_user == "ordex"

    def test_http_rpc_context_url_with_wallet(self):
        from ordex_web_wallet.rpc import HTTPRPCContext

        ctx = HTTPRPCContext(
            "ordexcoin", "wallet_1_ordexcoin", "ordex", "password", 5332, "localhost"
        )

        assert "wallet_1_ordexcoin" in ctx.url

    def test_http_rpc_context_url_without_wallet(self):
        from ordex_web_wallet.rpc import HTTPRPCContext

        ctx = HTTPRPCContext("ordexcoin", None, "ordex", "password", 5332, "localhost")

        assert "wallet" not in ctx.url.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
