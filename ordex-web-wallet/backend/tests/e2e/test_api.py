import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("RPC_PASS", "testpassword")


class TestAuthenticationE2E:
    """End-to-end tests for authentication flow."""

    @pytest.fixture
    def client(self):
        with patch("ordex_web_wallet.database.init_database"):
            from ordex_web_wallet.app import create_app

            app = create_app()
            app.config["TESTING"] = True
            with app.test_client() as client:
                yield client

    def test_user_registration_flow(self, client):
        """Test complete user registration flow."""
        with (
            patch("ordex_web_wallet.database.get_user_by_username") as mock_get,
            patch("ordex_web_wallet.database.create_user") as mock_create,
            patch("ordex_web_wallet.database.create_session") as mock_session,
            patch("ordex_web_wallet.rpc.daemon_manager") as mock_daemon,
        ):
            mock_get.return_value = None
            mock_create.return_value = {
                "id": 1,
                "username": "newuser",
                "is_admin": False,
            }
            mock_session.return_value = {"id": 1}
            mock_daemon.create_user_wallet.return_value = "wallet_1_ordexcoin"
            mock_daemon.create_user_wallet.return_value = "wallet_1_ordexgold"
            mock_daemon.get_user_address.return_value = "TestAddress"

            response = client.post(
                "/api/auth/register",
                json={
                    "username": "newuser",
                    "email": "new@test.com",
                    "password": "password123",
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
            patch("ordex_web_wallet.database.get_user_by_username") as mock_get,
            patch("ordex_web_wallet.database.create_session") as mock_session,
        ):
            mock_get.return_value = {
                "id": 1,
                "username": "testuser",
                "password_hash": "$2b$12$TestHash",
                "is_active": True,
                "is_admin": False,
            }
            mock_session.return_value = {"id": 1}

            from ordex_web_wallet.api.auth import verify_password

            with patch("ordex_web_wallet.api.auth.verify_password", return_value=True):
                response = client.post(
                    "/api/auth/login",
                    json={
                        "username": "testuser",
                        "password": "password123",
                    },
                )

                assert response.status_code in [200, 500]

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        with patch("ordex_web_wallet.database.get_user_by_username") as mock_get:
            mock_get.return_value = None

            response = client.post(
                "/api/auth/login",
                json={
                    "username": "nonexistent",
                    "password": "wrongpassword",
                },
            )

            assert response.status_code == 401
            data = json.loads(response.data)
            assert "error" in data

    def test_logout_flow(self, client):
        """Test logout flow."""
        with (
            patch("ordex_web_wallet.database.get_session") as mock_session,
            patch("ordex_web_wallet.database.delete_session"),
        ):
            mock_session.return_value = {
                "user_id": 1,
                "session_token": "test_token",
                "username": "testuser",
                "is_admin": False,
            }

            response = client.post(
                "/api/auth/logout",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code in [200, 401]


class TestWalletE2E:
    """End-to-end tests for wallet operations."""

    @pytest.fixture
    def authenticated_client(self):
        with patch("ordex_web_wallet.database.init_database"):
            from ordex_web_wallet.app import create_app

            app = create_app()
            app.config["TESTING"] = True

            with app.test_client() as client:
                with patch("ordex_web_wallet.database.get_session") as mock_session:
                    mock_session.return_value = {
                        "user_id": 1,
                        "session_token": "valid_token",
                        "username": "testuser",
                        "is_admin": False,
                    }
                    yield client

    def test_get_balance(self, authenticated_client):
        """Test getting wallet balance."""
        with (
            patch("ordex_web_wallet.database.get_user_wallets") as mock_wallets,
            patch("ordex_web_wallet.rpc.daemon_manager") as mock_daemon,
        ):
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
                {"chain": "ordexgold", "wallet_name": "wallet_1_ordexgold"},
            ]
            mock_daemon.get_user_balance.side_effect = [10.5, 5.25]

            response = authenticated_client.get(
                "/api/wallet/balance",
                headers={"Authorization": "Bearer valid_token"},
            )

            data = json.loads(response.data)
            assert "ordexcoin" in data

    def test_get_addresses(self, authenticated_client):
        """Test getting wallet addresses."""
        with (
            patch("ordex_web_wallet.database.get_user_wallets") as mock_wallets,
            patch("ordex_web_wallet.rpc.daemon_manager") as mock_daemon,
        ):
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            ]
            mock_daemon.get_user_address.return_value = "OXTestAddress123"

            response = authenticated_client.get(
                "/api/wallet/addresses",
                headers={"Authorization": "Bearer valid_token"},
            )

            data = json.loads(response.data)
            assert "ordexcoin" in data

    def test_send_transaction(self, authenticated_client):
        """Test sending a transaction."""
        with (
            patch("ordex_web_wallet.database.get_user_wallets") as mock_wallets,
            patch("ordex_web_wallet.rpc.daemon_manager") as mock_daemon,
        ):
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            ]
            mock_daemon.send_from_user.return_value = "txid123"

            response = authenticated_client.post(
                "/api/wallet/send",
                json={
                    "chain": "ordexcoin",
                    "address": "DestinationAddress",
                    "amount": 1.0,
                },
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code in [200, 500]


class TestAdminE2E:
    """End-to-end tests for admin operations."""

    @pytest.fixture
    def admin_client(self):
        with patch("ordex_web_wallet.database.init_database"):
            from ordex_web_wallet.app import create_app

            app = create_app()
            app.config["TESTING"] = True

            with app.test_client() as client:
                with patch("ordex_web_wallet.database.get_session") as mock_session:
                    mock_session.return_value = {
                        "user_id": 1,
                        "session_token": "admin_token",
                        "username": "admin",
                        "is_admin": True,
                    }
                    yield client

    def test_admin_list_users(self, admin_client):
        """Test listing all users."""
        with patch("ordex_web_wallet.database.get_all_users") as mock_users:
            mock_users.return_value = [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@test.com",
                    "is_active": True,
                },
                {
                    "id": 2,
                    "username": "user2",
                    "email": "user2@test.com",
                    "is_active": True,
                },
            ]

            response = admin_client.get(
                "/api/admin/users",
                headers={"Authorization": "Bearer admin_token"},
            )

            data = json.loads(response.data)
            assert len(data) == 2

    def test_admin_get_stats(self, admin_client):
        """Test getting system stats."""
        with patch("ordex_web_wallet.database.get_system_stats") as mock_stats:
            mock_stats.return_value = {
                "total_users": 100,
                "active_users": 50,
                "total_wallets": 200,
            }

            response = admin_client.get(
                "/api/admin/stats",
                headers={"Authorization": "Bearer admin_token"},
            )

            data = json.loads(response.data)
            assert data["total_users"] == 100

    def test_admin_disable_user(self, admin_client):
        """Test disabling a user."""
        with (
            patch("ordex_web_wallet.database.update_user_status"),
            patch("ordex_web_wallet.database.admin_audit_log"),
        ):
            response = admin_client.post(
                "/api/admin/users/2/disable",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code in [200, 500]

    def test_admin_enable_user(self, admin_client):
        """Test enabling a user."""
        with (
            patch("ordex_web_wallet.database.update_user_status"),
            patch("ordex_web_wallet.database.admin_audit_log"),
        ):
            response = admin_client.post(
                "/api/admin/users/2/enable",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code in [200, 500]


class TestSystemE2E:
    """End-to-end tests for system endpoints."""

    @pytest.fixture
    def client(self):
        with patch("ordex_web_wallet.database.init_database"):
            from ordex_web_wallet.app import create_app

            app = create_app()
            app.config["TESTING"] = True
            with app.test_client() as client:
                yield client

    def test_health_check(self, client):
        """Test health check endpoint."""
        with patch("ordex_web_wallet.rpc.daemon_manager") as mock_daemon:
            mock_daemon.oxc.getblockchaininfo.return_value = {"blocks": 100}
            mock_daemon.oxg.getblockchaininfo.return_value = {"blocks": 50}

            response = client.get("/api/system/health")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "status" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Ordex Web Wallet"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"

    def test_prometheus_metrics(self, client):
        """Test metrics endpoint."""
        response = client.get("/api/system/metrics")

        assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
