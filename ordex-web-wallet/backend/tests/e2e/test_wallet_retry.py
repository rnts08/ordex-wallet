import pytest
import json
from unittest.mock import patch, MagicMock

class TestWalletRetryWorkflowE2E:
    """End-to-end tests for wallet creation retry logic during login."""

    def test_login_retries_missing_wallets(self, client):
        """Test that login correctly retries wallet creation if missing from DB."""
        # 1. Setup existing user with NO wallets in DB
        with patch("ordex_web_wallet.api.auth.get_user_by_username") as mock_get_user, \
             patch("ordex_web_wallet.api.auth.verify_password", return_value=True), \
             patch("ordex_web_wallet.api.auth.get_user_wallets", return_value=[]), \
             patch("ordex_web_wallet.rpc.daemon_manager.create_user_wallet", return_value="wallet_1_oxc"), \
             patch("ordex_web_wallet.api.auth.create_user_wallet") as mock_create_db, \
             patch("ordex_web_wallet.api.auth.create_session"):

            mock_get_user.return_value = {
                "id": 1, "username": "retryuser", "password_hash": "hash", "is_admin": False, "is_active": True
            }

            # 2. Perform Login
            response = client.post(
                "/api/auth/login",
                json={"username": "retryuser", "password": "Password123!"}
            )

            assert response.status_code == 200
            # Verify retry logic was called twice (once for each chain)
            assert mock_create_db.call_count == 2

    def test_login_disables_account_on_retry_failure(self, client):
        """Test that login disables the account if wallet creation fails again."""
        # 1. Setup existing user with NO wallets in DB
        with patch("ordex_web_wallet.api.auth.get_user_by_username") as mock_get_user, \
             patch("ordex_web_wallet.api.auth.verify_password", return_value=True), \
             patch("ordex_web_wallet.api.auth.get_user_wallets", return_value=[]), \
             patch("ordex_web_wallet.rpc.daemon_manager.create_user_wallet", side_effect=Exception("RPC Error")), \
             patch("ordex_web_wallet.api.auth.update_user_status") as mock_disable:

            mock_get_user.return_value = {
                "id": 1, "username": "failuser", "password_hash": "hash", "is_admin": False, "is_active": True
            }

            # 2. Perform Login
            response = client.post(
                "/api/auth/login",
                json={"username": "failuser", "password": "Password123!"}
            )

            assert response.status_code == 500
            assert "Account has been disabled" in json.loads(response.data)["error"]
            # Verify account was disabled
            mock_disable.assert_called_with(1, False)
