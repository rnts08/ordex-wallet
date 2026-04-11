import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("RPC_PASS", "testpassword")


@pytest.fixture
def mock_db():
    with patch("ordex_web_wallet.database.init_database"), \
         patch("ordex_web_wallet.database.DATABASE.execute_one") as m_one, \
         patch("ordex_web_wallet.database.DATABASE.execute") as m_all, \
         patch("ordex_web_wallet.database.DATABASE.execute_write") as m_write:
        m_one.return_value = {
            "id": 1, 
            "user_id": 1, 
            "username": "testuser", 
            "password_hash": "scrypt:32768:8:1$hash", 
            "session_token": "valid_token",
            "is_admin": False, 
            "is_active": True,
            "count": 0,
            "size": 1000
        }
        m_all.return_value = []
        m_write.return_value = 1
        yield


@pytest.fixture
def mock_rpc():
    # Patch in rpc module where it's defined
    with patch("ordex_web_wallet.rpc.daemon_manager") as mock:
        # Also patch in modules that have already imported it at top-level
        with patch("ordex_web_wallet.api.auth.daemon_manager", mock), \
             patch("ordex_web_wallet.api.wallet.daemon_manager", mock), \
             patch("ordex_web_wallet.api.admin.daemon_manager", mock):
            
            mock.oxc.getblockchaininfo.return_value = {"blocks": 100}
            mock.oxg.getblockchaininfo.return_value = {"blocks": 50}
            mock.create_user_wallet.return_value = "wallet_1_ordexcoin"
            mock.get_user_address.return_value = "TestAddress123"
            mock.get_user_balance.return_value = 0.0
            
            yield mock


@pytest.fixture
def app(mock_db, mock_rpc):
    from ordex_web_wallet.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_token(mock_db):
    from ordex_web_wallet.middleware.auth import create_session_token
    token = create_session_token()

    with patch("ordex_web_wallet.middleware.auth.get_session") as mock_session, \
         patch("ordex_web_wallet.middleware.auth.clean_expired_sessions"):
        
        admin_data = {
            "id": 1,
            "user_id": 1,
            "username": "admin",
            "session_token": token,
            "is_admin": True,
            "is_active": True
        }
        
        mock_session.return_value = admin_data
        yield token


@pytest.fixture
def user_token(mock_db):
    from ordex_web_wallet.middleware.auth import create_session_token
    token = create_session_token()

    with patch("ordex_web_wallet.middleware.auth.get_session") as mock_session:
        mock_session.return_value = {
            "user_id": 2,
            "session_token": token,
            "username": "testuser",
            "is_admin": False,
            "is_active": True
        }
        yield token
