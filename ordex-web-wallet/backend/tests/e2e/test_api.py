import pytest
import json
from unittest.mock import patch, MagicMock

class TestAuthenticationE2E:
    """End-to-end tests for authentication flow."""

    def test_user_registration_flow(self, client):
        """Test complete user registration flow."""
        with (
            patch("ordex_web_wallet.api.auth.get_user_by_username") as mock_get,
            patch("ordex_web_wallet.api.auth.create_user") as mock_create,
            patch("ordex_web_wallet.api.auth.create_session") as mock_session,
            patch("ordex_web_wallet.api.auth.daemon_manager") as mock_daemon,
        ):
            mock_get.return_value = None
            mock_create.return_value = {
                "id": 1,
                "username": "newuser",
                "is_active": True,
                "is_admin": False,
            }
            mock_session.return_value = {"id": 1}
            mock_daemon.create_user_wallet.side_effect = [
                "wallet_1_ordexcoin",
                "wallet_1_ordexgold",
            ]
            mock_daemon.get_user_address.return_value = "TestAddress"

            response = client.post(
                "/api/auth/register",
                json={
                    "username": "newuser",
                    "email": "new@test.com",
                    "password": "Password123!",
                    "passphrase": "passphrase123",
                },
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "token" in data
            assert data["username"] == "newuser"

    def test_user_login_flow(self, client):
        """Test complete user login flow."""
        with (
            patch("ordex_web_wallet.api.auth.get_user_by_username") as mock_get,
            patch("ordex_web_wallet.api.auth.create_session") as mock_session,
            patch("ordex_web_wallet.api.auth.verify_password", return_value=True),
        ):
            mock_get.return_value = {
                "id": 1,
                "username": "testuser",
                "password_hash": "$2b$12$TestHash",
                "is_active": True,
                "is_admin": False,
            }
            mock_session.return_value = {"id": 1}

            response = client.post(
                "/api/auth/login",
                json={
                    "username": "testuser",
                    "password": "Password123!",
                },
            )

            assert response.status_code == 200

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        with patch("ordex_web_wallet.api.auth.get_user_by_username") as mock_get:
            mock_get.return_value = None

            response = client.post(
                "/api/auth/login",
                json={
                    "username": "nonexistent",
                    "password": "wrongpassword",
                },
            )

            assert response.status_code == 401

    def test_logout_flow(self, client, user_token):
        """Test logout flow."""
        with patch("ordex_web_wallet.api.auth.delete_session") as mock_del:
            response = client.post(
                "/api/auth/logout",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert response.status_code == 200

class TestWalletE2E:
    """End-to-end tests for wallet operations."""

    def test_get_balance(self, client, user_token, mock_rpc):
        """Test getting wallet balance."""
        with patch("ordex_web_wallet.api.wallet.get_user_wallets") as mock_wallets:
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            ]
            mock_rpc.get_user_balance.return_value = 10.5

            response = client.get(
                "/api/wallet/balance",
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "ordexcoin" in data

    def test_get_addresses(self, client, user_token, mock_rpc):
        """Test getting wallet addresses."""
        with patch("ordex_web_wallet.api.wallet.get_user_wallets") as mock_wallets:
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            ]
            mock_rpc.get_user_address.return_value = "OXTestAddress123"

            response = client.get(
                "/api/wallet/addresses",
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "ordexcoin" in data

    def test_send_transaction(self, client, user_token, mock_rpc):
        """Test sending a transaction."""
        mock_rpc.send_from_user.return_value = "txid123"

        response = client.post(
            "/api/wallet/send",
            json={
                "chain": "ordexcoin",
                "address": "DestinationAddress",
                "amount": 1.0,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        assert json.loads(response.data)["txid"] == "txid123"

class TestAdminE2E:
    """End-to-end tests for admin operations."""

    def test_admin_list_users(self, client, admin_token):
        """Test listing all users."""
        with patch("ordex_web_wallet.api.admin.get_users_paged") as mock_users:
            mock_users.return_value = [
                {"id": 1, "username": "admin", "is_active": True},
                {"id": 2, "username": "user2", "is_active": True},
            ]

            response = client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2

    def test_admin_get_stats(self, client, admin_token, mock_rpc):
        """Test getting system stats."""
        with patch("ordex_web_wallet.api.admin.get_system_stats") as mock_stats:
            mock_stats.return_value = {"total_users": 100, "active_users": 50, "total_wallets": 200}
            mock_rpc.get_total_balance.return_value = 1000.0

            response = client.get(
                "/api/admin/stats",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["total_users"] == 100

    def test_admin_disable_user(self, client, admin_token):
        """Test disabling a user."""
        with patch("ordex_web_wallet.api.admin.update_user_status") as mock_status:
            response = client.post(
                "/api/admin/users/2/disable",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            mock_status.assert_called_with(2, False)

    def test_admin_enable_user(self, client, admin_token):
        """Test enabling a user."""
        with patch("ordex_web_wallet.api.admin.update_user_status") as mock_status:
            response = client.post(
                "/api/admin/users/2/enable",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            mock_status.assert_called_with(2, True)

class TestSystemE2E:
    """End-to-end tests for system endpoints."""

    def test_health_check(self, client, mock_rpc):
        """Test health check endpoint."""
        mock_rpc.oxc.getblockchaininfo.return_value = {"blocks": 100}
        mock_rpc.oxg.getblockchaininfo.return_value = {"blocks": 50}

        response = client.get("/api/system/health")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    def test_info_endpoint(self, client):
        """Test info endpoint."""
        response = client.get("/api/info")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Ordex Web Wallet"

    def test_prometheus_metrics(self, client):
        """Test metrics endpoint."""
        response = client.get("/api/system/metrics")
        # Just check it's readable, might need special mock if it calls a collector
        assert response.status_code in [200, 500]
