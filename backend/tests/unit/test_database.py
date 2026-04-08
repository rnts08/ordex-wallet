"""
Unit tests for Database Module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from database import Database, DatabaseManager


class TestDatabase(unittest.TestCase):
    """Test cases for Database class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test database initialization."""
        db = Database(str(self.db_path))
        self.assertTrue(self.db_path.exists())
        db.close()

    def test_get_setting(self):
        """Test getting a setting."""
        db = Database(str(self.db_path))
        result = db.get_setting("test_key")
        self.assertIsNone(result)
        db.close()

    def test_set_setting(self):
        """Test setting a value."""
        db = Database(str(self.db_path))
        db.set_setting("test_key", "test_value")
        result = db.get_setting("test_key")
        self.assertEqual(result, "test_value")
        db.close()

    def test_get_all_settings(self):
        """Test getting all settings."""
        db = Database(str(self.db_path))
        db.set_setting("key1", "value1")
        db.set_setting("key2", "value2")
        settings = db.get_all_settings()
        self.assertEqual(settings["key1"], "value1")
        self.assertEqual(settings["key2"], "value2")
        db.close()

    def test_has_wallet_false(self):
        """Test has_wallet returns false initially."""
        db = Database(str(self.db_path))
        self.assertFalse(db.has_wallet())
        db.close()

    def test_has_wallet_true(self):
        """Test has_wallet returns true after creating wallet."""
        db = Database(str(self.db_path))
        db.create_wallet()
        self.assertTrue(db.has_wallet())
        db.close()

    def test_create_wallet(self):
        """Test wallet creation."""
        db = Database(str(self.db_path))
        db.create_wallet("passphrase_hash")
        meta = db.get_wallet_meta()
        self.assertIsNotNone(meta)
        self.assertEqual(meta["has_wallet"], 1)
        self.assertEqual(meta["backup_passphrase_hash"], "passphrase_hash")
        db.close()

    def test_delete_wallet(self):
        """Test wallet deletion."""
        db = Database(str(self.db_path))
        db.create_wallet()
        db.delete_wallet()
        self.assertFalse(db.has_wallet())
        db.close()

    def test_add_address(self):
        """Test adding an address."""
        db = Database(str(self.db_path))
        db.add_address("Mtest123", "ordexcoin", "Test Label", "default", False)
        addresses = db.get_addresses("ordexcoin")
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0]["address"], "Mtest123")
        self.assertEqual(addresses[0]["label"], "Test Label")
        db.close()

    def test_get_addresses_filter(self):
        """Test getting addresses with filters."""
        db = Database(str(self.db_path))
        db.add_address("Mtest1", "ordexcoin", "", "", False)
        db.add_address("Mtest2", "ordexcoin", "", "", True)

        receive = db.get_addresses(network="ordexcoin", is_change=False)
        self.assertEqual(len(receive), 1)

        change = db.get_addresses(network="ordexcoin", is_change=True)
        self.assertEqual(len(change), 1)
        db.close()

    def test_add_transaction(self):
        """Test adding a transaction."""
        db = Database(str(self.db_path))
        db.add_transaction(
            "txid123",
            "ordexcoin",
            "Maddress",
            1.0,
            0.001,
            "receive",
            6,
            "blockhash",
            1234567890,
            1234567890,
        )
        tx = db.get_transaction("txid123")
        self.assertIsNotNone(tx)
        self.assertEqual(tx["amount"], 1.0)
        self.assertEqual(tx["confirmations"], 6)
        db.close()

    def test_get_transactions(self):
        """Test getting transactions."""
        db = Database(str(self.db_path))
        db.add_transaction("tx1", "ordexcoin", "Maddr", 1.0, 0.001, "receive")
        db.add_transaction("tx2", "ordexcoin", "Maddr", -0.5, 0.001, "send")
        db.add_transaction("tx3", "ordexgold", "Gaddr", 2.0, 0.001, "receive")

        all_txs = db.get_transactions()
        self.assertEqual(len(all_txs), 3)

        oxc_txs = db.get_transactions(network="ordexcoin")
        self.assertEqual(len(oxc_txs), 2)

        send_txs = db.get_transactions(category="send")
        self.assertEqual(len(send_txs), 1)
        db.close()

    def test_add_audit_log(self):
        """Test adding audit log."""
        db = Database(str(self.db_path))
        db.add_audit_log("INFO", "wallet", "Wallet created", {"user": "test"})
        logs = db.get_audit_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["level"], "INFO")
        self.assertEqual(logs[0]["category"], "wallet")
        db.close()

    def test_get_audit_logs_filters(self):
        """Test getting audit logs with filters."""
        db = Database(str(self.db_path))
        db.add_audit_log("INFO", "wallet", "Message 1")
        db.add_audit_log("ERROR", "rpc", "Message 2")

        info_logs = db.get_audit_logs(level="INFO")
        self.assertEqual(len(info_logs), 1)

        wallet_logs = db.get_audit_logs(category="wallet")
        self.assertEqual(len(wallet_logs), 1)
        db.close()


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test database manager initialization."""
        manager = DatabaseManager(self.temp_dir)
        self.assertIsNotNone(manager.main_db)
        manager.close()

    def test_get_db(self):
        """Test getting database instance."""
        manager = DatabaseManager(self.temp_dir)
        db = manager.get_db()
        self.assertIsInstance(db, Database)
        manager.close()


if __name__ == "__main__":
    unittest.main()
