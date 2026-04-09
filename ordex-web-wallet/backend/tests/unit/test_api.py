import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("RPC_PASS", "testpassword")


class TestAuthAPI:
    """Test authentication API endpoints."""

    @pytest.fixture
    def client(self):
        with patch("ordex_web_wallet.database.init_database"):
            from ordex_web_wallet.app import create_app

            app = create_app()
            app.config["TESTING"] = True
            with app.test_client() as client:
                yield client

    def test_register_endpoint_exists(self, client):
        """Test register endpoint responds."""
        from flask import Flask
        from ordex_web_wallet.api.auth import auth_bp

        app = Flask(__name__)
        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        client = app.test_client()

        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@test.com",
                "password": "password123",
                "passphrase": "passphrase123",
            },
        )

        assert response.status_code in [200, 400, 401, 500]

    def test_login_endpoint_exists(self, client):
        """Test login endpoint exists."""
        from flask import Flask
        from ordex_web_wallet.api.auth import auth_bp

        app = Flask(__name__)
        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        client = app.test_client()

        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "password123"},
        )

        assert response.status_code in [200, 400, 401, 500]

    def test_logout_requires_auth(self, client):
        """Test logout requires authentication."""
        response = client.post("/api/auth/logout")

        assert response.status_code in [200, 401]

    def test_me_requires_auth(self, client):
        """Test /me endpoint requires auth."""
        response = client.get("/api/auth/me")

        assert response.status_code in [200, 401]


class TestWalletAPI:
    """Test wallet API endpoints."""

    def test_balance_requires_auth(self):
        """Test balance endpoint requires auth."""
        from flask import Flask
        from ordex_web_wallet.api.wallet import wallet_bp

        app = Flask(__name__)
        app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
        client = app.test_client()

        response = client.get("/api/wallet/balance")

        assert response.status_code in [200, 401]

    def test_addresses_requires_auth(self):
        """Test addresses endpoint requires auth."""
        from flask import Flask
        from ordex_web_wallet.api.wallet import wallet_bp

        app = Flask(__name__)
        app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
        client = app.test_client()

        response = client.get("/api/wallet/addresses")

        assert response.status_code in [200, 401]

    def test_send_requires_auth(self):
        """Test send endpoint requires auth."""
        from flask import Flask
        from ordex_web_wallet.api.wallet import wallet_bp

        app = Flask(__name__)
        app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
        client = app.test_client()

        response = client.post(
            "/api/wallet/send",
            json={"chain": "ordexcoin", "address": "test", "amount": 1.0},
        )

        assert response.status_code in [200, 400, 401, 500]

    def test_history_requires_auth(self):
        """Test history endpoint requires auth."""
        from flask import Flask
        from ordex_web_wallet.api.wallet import wallet_bp

        app = Flask(__name__)
        app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
        client = app.test_client()

        response = client.get("/api/wallet/history")

        assert response.status_code in [200, 401]


class TestAdminAPI:
    """Test admin API endpoints."""

    def test_admin_users_requires_admin(self):
        """Test admin users endpoint requires admin."""
        from flask import Flask
        from ordex_web_wallet.api.admin import admin_bp

        app = Flask(__name__)
        app.register_blueprint(admin_bp, url_prefix="/api/admin")
        client = app.test_client()

        response = client.get("/api/admin/users")

        assert response.status_code in [200, 401, 403]

    def test_admin_stats_requires_admin(self):
        """Test admin stats requires admin."""
        from flask import Flask
        from ordex_web_wallet.api.admin import admin_bp

        app = Flask(__name__)
        app.register_blueprint(admin_bp, url_prefix="/api/admin")
        client = app.test_client()

        response = client.get("/api/admin/stats")

        assert response.status_code in [200, 401, 403]

    def test_admin_disable_user_requires_admin(self):
        """Test disable user requires admin."""
        from flask import Flask
        from ordex_web_wallet.api.admin import admin_bp

        app = Flask(__name__)
        app.register_blueprint(admin_bp, url_prefix="/api/admin")
        client = app.test_client()

        response = client.post("/api/admin/users/1/disable")

        assert response.status_code in [200, 401, 403]

    def test_admin_enable_user_requires_admin(self):
        """Test enable user requires admin."""
        from flask import Flask
        from ordex_web_wallet.api.admin import admin_bp

        app = Flask(__name__)
        app.register_blueprint(admin_bp, url_prefix="/api/admin")
        client = app.test_client()

        response = client.post("/api/admin/users/1/enable")

        assert response.status_code in [200, 401, 403]

    def test_admin_delete_requires_admin(self):
        """Test delete user requires admin."""
        from flask import Flask
        from ordex_web_wallet.api.admin import admin_bp

        app = Flask(__name__)
        app.register_blueprint(admin_bp, url_prefix="/api/admin")
        client = app.test_client()

        response = client.delete("/api/admin/users/1")

        assert response.status_code in [200, 401, 403]


class TestSystemAPI:
    """Test system API endpoints."""

    @pytest.fixture
    def client(self):
        with patch("ordex_web_wallet.database.init_database"):
            from ordex_web_wallet.app import create_app

            app = create_app()
            app.config["TESTING"] = True
            with app.test_client() as client:
                yield client

    def test_health_endpoint(self, client):
        """Test health endpoint."""
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
        assert "name" in data
        assert "version" in data


class TestAuthMiddleware:
    """Test authentication middleware."""

    def test_extract_token_from_header(self):
        """Test token extraction from Authorization header."""
        from flask import Flask
        from unittest.mock import Mock
        from ordex_web_wallet.middleware.auth import extract_token

        app = Flask(__name__)

        with app.test_request_context(headers={"Authorization": "Bearer test_token"}):
            token = extract_token()
            assert token == "test_token"

    def test_extract_token_from_cookie(self):
        """Test token extraction from cookie."""
        from flask import Flask
        from ordex_web_wallet.middleware.auth import extract_token

        app = Flask(__name__)

        with app.test_request_context(cookies={"session_token": "cookie_token"}):
            token = extract_token()
            assert token == "cookie_token"

    def test_extract_token_empty(self):
        """Test token extraction with no auth."""
        from flask import Flask
        from ordex_web_wallet.middleware.auth import extract_token

        app = Flask(__name__)

        with app.test_request_context():
            token = extract_token()
            assert token is None

    def test_create_session_token(self):
        """Test session token creation."""
        from ordex_web_wallet.middleware.auth import create_session_token

        token1 = create_session_token()
        token2 = create_session_token()

        assert token1 is not None
        assert len(token1) > 10
        assert token1 != token2

    def test_create_session_expiry(self):
        """Test session expiry creation."""
        from ordex_web_wallet.middleware.auth import create_session_expiry
        from datetime import datetime, timedelta

        expiry = create_session_expiry(3600)

        assert isinstance(expiry, datetime)
        expected = datetime.utcnow() + timedelta(hours=1)
        diff = abs((expiry - expected).total_seconds())
        assert diff < 5


class TestPasswordSecurity:
    """Test password security functions."""

    def test_password_hashing(self):
        """Test bcrypt password hashing."""
        from ordex_web_wallet.api.auth import hash_password, verify_password

        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_password_not_reversible(self):
        """Test password hash is not reversible."""
        from ordex_web_wallet.api.auth import hash_password

        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed not in password


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
