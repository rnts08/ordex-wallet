#!/usr/bin/env python3

import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

# Mock config to avoid import issues
import unittest.mock as mock

sys.modules["ordex_web_wallet.config"] = mock.MagicMock()
sys.modules["ordex_web_wallet.config"].SECRET_KEY = "test-secret"
sys.modules["ordex_web_wallet.config"].DEBUG = False


def test_get_or_create_user_address():
    from backend.rpc import DaemonManager

    # Mock the CLIContext
    with mock.patch("backend.rpc.CLIContext") as mock_ctx_class:
        mock_ctx = MagicMock()
        mock_ctx_class.return_value = mock_ctx

        # Test case 1: Empty address list -> should create new address
        mock_ctx.call.side_effect = [
            [],  # listaddressgroupings returns empty list
            "new_address_123",  # getnewaddress returns new address
        ]

        dm = DaemonManager("/fake/path", "ordex", "ordexpass", "/data")
        result = dm.get_or_create_user_address(1, "ordexcoin")

        assert result == "new_address_123"
        assert mock_ctx.call.call_count == 2
        mock_ctx.call.assert_any_call("listaddressgroupings")
        mock_ctx.call.assert_any_call("getnewaddress", "")

        # Reset mock
        mock_ctx.reset_mock()
        mock_ctx.call.side_effect = [
            [
                [["addr1", 1.0, "label"], ["addr2", 0.5, "label2"]]
            ],  # listaddressgroupings with data
        ]

        # Test case 2: Existing addresses -> should return first address
        result = dm.get_or_create_user_address(2, "ordexgold")

        assert result == "addr1"
        assert mock_ctx.call.call_count == 1
        mock_ctx.call.assert_called_with("listaddressgroupings")

        print("All tests passed!")


if __name__ == "__main__":
    test_get_or_create_user_address()
