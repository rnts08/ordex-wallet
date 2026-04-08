"""
Unit tests for Backup Service.
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from services.backup import BackupService


class TestBackupService(unittest.TestCase):
    """Test cases for BackupService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_service = BackupService(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test backup service initialization."""
        backup_dir = Path(self.temp_dir) / "backups"
        self.assertTrue(backup_dir.exists())

    def test_create_backup_no_passphrase(self):
        """Test creating backup without passphrase."""
        backup_path = self.backup_service.create_backup()

        self.assertTrue(os.path.exists(backup_path))
        self.assertTrue(backup_path.endswith(".json"))

    def test_create_backup_with_passphrase(self):
        """Test creating encrypted backup with passphrase."""
        backup_path = self.backup_service.create_backup("test_passphrase")

        self.assertTrue(os.path.exists(backup_path))
        self.assertTrue(backup_path.endswith(".enc"))

    def test_restore_backup_encrypted(self):
        """Test restoring encrypted backup."""
        backup_path = self.backup_service.create_backup("test_passphrase")

        with open(backup_path, "rb") as f:
            data = f.read()

        result = self.backup_service.restore_backup(data, "test_passphrase")
        self.assertTrue(result)

    def test_restore_backup_wrong_passphrase(self):
        """Test restoring backup with wrong passphrase."""
        backup_path = self.backup_service.create_backup("correct_passphrase")

        with open(backup_path, "rb") as f:
            data = f.read()

        with self.assertRaises(ValueError):
            self.backup_service.restore_backup(data, "wrong_passphrase")

    def test_verify_backup_valid(self):
        """Test verifying valid backup."""
        backup_path = self.backup_service.create_backup("pass123")

        result = self.backup_service.verify_backup(backup_path, "pass123")
        self.assertTrue(result)

    def test_verify_backup_invalid_passphrase(self):
        """Test verifying backup with invalid passphrase."""
        backup_path = self.backup_service.create_backup("correct_pass")

        result = self.backup_service.verify_backup(backup_path, "wrong_pass")
        self.assertFalse(result)

    def test_list_backups(self):
        """Test listing backups."""
        self.backup_service.create_backup()
        self.backup_service.create_backup()

        backups = self.backup_service.list_backups()

        self.assertEqual(len(backups), 2)
        self.assertIn("filename", backups[0])
        self.assertIn("size", backups[0])
        self.assertIn("created", backups[0])

    def test_cleanup_old_backups(self):
        """Test old backup cleanup."""
        for _ in range(10):
            self.backup_service.create_backup()

        backups = self.backup_service.list_backups()
        self.assertEqual(len(backups), 7)

    def test_xor_encrypt_decrypt(self):
        """Test XOR encryption and decryption."""
        data = "test data"
        key = b"testkey"

        encrypted = self.backup_service._xor_encrypt(data, key)
        decrypted = self.backup_service._xor_decrypt(encrypted, key)

        self.assertEqual(decrypted, data)


if __name__ == "__main__":
    unittest.main()
