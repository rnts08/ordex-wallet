import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("RPC_PASS", "testpassword")


class TestDatabaseSchema:
    """Test database schema and migration system."""

    @patch("ordex_web_wallet.database.DATABASE")
    def test_schema_version_tracking(self, mock_db):
        from ordex_web_wallet.database import SCHEMA_VERSION, get_schema_version

        assert SCHEMA_VERSION >= 1
        mock_db.execute_one.return_value = {"version": 1}
        assert get_schema_version() == 1

    @patch("ordex_web_wallet.database.DATABASE")
    def test_migrations_list_not_empty(self, mock_db):
        from ordex_web_wallet.database import MIGRATIONS

        assert len(MIGRATIONS) > 0
        version, sql = MIGRATIONS[0]
        assert version == 1
        assert "CREATE TABLE" in sql

    @patch("ordex_web_wallet.database.DATABASE")
    def test_schema_includes_migrations_table(self, mock_db):
        from ordex_web_wallet.database import SCHEMA

        assert "schema_migrations" in SCHEMA
        assert "CREATE TABLE IF NOT EXISTS users" in SCHEMA
        assert "CREATE TABLE IF NOT EXISTS sessions" in SCHEMA

    @patch("ordex_web_wallet.database.DATABASE")
    def test_schema_includes_all_tables(self, mock_db):
        from ordex_web_wallet.database import SCHEMA

        required_tables = [
            "users",
            "user_wallets",
            "sessions",
            "user_settings",
            "address_book",
            "transactions",
            "admin_audit",
        ]
        for table in required_tables:
            assert f"CREATE TABLE IF NOT EXISTS {table}" in SCHEMA

    @patch("ordex_web_wallet.database.DATABASE")
    def test_schema_includes_indexes(self, mock_db):
        from ordex_web_wallet.database import SCHEMA

        assert "CREATE INDEX" in SCHEMA
        assert "idx_sessions_token" in SCHEMA
        assert "idx_sessions_expires" in SCHEMA

    @patch("ordex_web_wallet.database.DATABASE")
    def test_user_table_structure(self, mock_db):
        from ordex_web_wallet.database import SCHEMA

        assert "username TEXT UNIQUE NOT NULL" in SCHEMA
        assert "email TEXT UNIQUE NOT NULL" in SCHEMA
        assert "password_hash TEXT NOT NULL" in SCHEMA
        assert "is_admin BOOLEAN DEFAULT FALSE" in SCHEMA
        assert "is_active BOOLEAN DEFAULT TRUE" in SCHEMA


class TestDatabaseOperations:
    """Test database CRUD operations."""

    @patch("ordex_web_wallet.database.DATABASE")
    def test_create_user(self, mock_db):
        from ordex_web_wallet.database import create_user

        mock_db.execute_one.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@test.com",
            "is_admin": False,
            "is_active": True,
        }

        result = create_user("testuser", "test@test.com", "hashed_password")

        assert result["username"] == "testuser"
        assert result["id"] == 1

    @patch("ordex_web_wallet.database.DATABASE")
    def test_get_user_by_username(self, mock_db):
        from ordex_web_wallet.database import get_user_by_username

        mock_db.execute_one.return_value = {
            "id": 1,
            "username": "testuser",
            "password_hash": "hashed",
        }

        result = get_user_by_username("testuser")

        assert result["username"] == "testuser"

    @patch("ordex_web_wallet.database.DATABASE")
    def test_get_session(self, mock_db):
        from ordex_web_wallet.database import get_session

        mock_db.execute_one.return_value = {
            "user_id": 1,
            "session_token": "test_token",
            "username": "testuser",
            "is_admin": False,
        }

        result = get_session("test_token")

        assert result["session_token"] == "test_token"

    @patch("ordex_web_wallet.database.DATABASE")
    def test_delete_session(self, mock_db):
        from ordex_web_wallet.database import delete_session

        delete_session("test_token")

        mock_db.execute_write.assert_called_once()

    @patch("ordex_web_wallet.database.DATABASE")
    def test_clean_expired_sessions(self, mock_db):
        from ordex_web_wallet.database import clean_expired_sessions

        clean_expired_sessions()

        mock_db.execute_write.assert_called_once()

    @patch("ordex_web_wallet.database.DATABASE")
    def test_create_user_wallet(self, mock_db):
        from ordex_web_wallet.database import create_user_wallet

        mock_db.execute_one.return_value = {
            "id": 1,
            "user_id": 1,
            "chain": "ordexcoin",
            "wallet_name": "wallet_1_ordexcoin",
        }

        result = create_user_wallet(1, "ordexcoin", "wallet_1_ordexcoin")

        assert result["wallet_name"] == "wallet_1_ordexcoin"

    @patch("ordex_web_wallet.database.DATABASE")
    def test_get_user_wallets(self, mock_db):
        from ordex_web_wallet.database import get_user_wallets

        mock_db.execute.return_value = [
            {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            {"chain": "ordexgold", "wallet_name": "wallet_1_ordexgold"},
        ]

        result = get_user_wallets(1)

        assert len(result) == 2

    @patch("ordex_web_wallet.database.DATABASE")
    def test_set_and_get_user_setting(self, mock_db):
        from ordex_web_wallet.database import set_user_setting, get_user_setting

        set_user_setting(1, "theme", "dark")

        mock_db.execute_one.assert_called()

        mock_db.execute_one.return_value = {"setting_value": "dark"}
        result = get_user_setting(1, "theme")

        assert result["setting_value"] == "dark"

    @patch("ordex_web_wallet.database.DATABASE")
    def test_update_user_status(self, mock_db):
        from ordex_web_wallet.database import update_user_status

        update_user_status(1, False)

        mock_db.execute_write.assert_called_once()

    @patch("ordex_web_wallet.database.DATABASE")
    def test_get_system_stats(self, mock_db):
        from ordex_web_wallet.database import get_system_stats

        mock_db.execute_one.return_value = {
            "total_users": 10,
            "active_users": 5,
            "active_24h": 2,
            "total_wallets": 20,
            "active_sessions": 3,
        }

        result = get_system_stats()

        assert result["total_users"] == 10
        assert result["active_users"] == 5

    @patch("ordex_web_wallet.database.DATABASE")
    def test_admin_audit_log(self, mock_db):
        from ordex_web_wallet.database import admin_audit_log

        admin_audit_log(1, "disable_user", 2, {"reason": "violation"})

        mock_db.execute_write.assert_called_once()


class TestDatabaseClass:
    """Test Database class functionality."""

    def test_database_init(self):
        from ordex_web_wallet.database import Database

        db = Database()

        assert db.database_url is not None

    @patch("ordex_web_wallet.database.get_database_config")
    def test_get_connection(self, mock_config):
        from ordex_web_wallet.database import Database

        mock_config.return_value = {
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        }

        db = Database()

        with patch("psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            db.get_connection()

            mock_connect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
