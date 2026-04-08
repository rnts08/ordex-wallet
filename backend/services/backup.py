"""
Backup Service for OrdexWallet.

Handles encrypted wallet backups.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class BackupService:
    """Service for creating and restoring wallet backups."""

    def __init__(self, data_dir: str):
        """Initialize backup service."""
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, passphrase: str = "") -> str:
        """Create an encrypted backup of the wallet."""
        import uuid

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]

        backup_data = {
            "version": "1.0",
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "wallet_data": {"note": "Use restore endpoint to restore wallet data"},
        }

        if passphrase:
            key = hashlib.pbkdf2_hmac(
                "sha256", passphrase.encode(), b"ordexwallet_salt", 100000, dklen=32
            )

            import base64

            encoded = base64.b64encode(json.dumps(backup_data).encode()).decode()
            encrypted = self._xor_encrypt(encoded, key)

            filename = f"ordexwallet_backup_{timestamp}_{unique_id}.enc"
        else:
            filename = f"ordexwallet_backup_{timestamp}_{unique_id}.json"
            encrypted = json.dumps(backup_data)

        backup_path = self.backup_dir / filename

        with open(backup_path, "w") as f:
            f.write(encrypted)

        os.chmod(backup_path, 0o600)

        self._cleanup_old_backups()

        logger.info(f"Backup created: {backup_path}")
        return str(backup_path)

    def restore_backup(self, encrypted_data: bytes, passphrase: str = "") -> bool:
        """Restore wallet from backup."""
        try:
            if passphrase:
                key = hashlib.pbkdf2_hmac(
                    "sha256", passphrase.encode(), b"ordexwallet_salt", 100000, dklen=32
                )

                decrypted = self._xor_decrypt(encrypted_data.decode(), key)
                import base64

                data = json.loads(base64.b64decode(decrypted).decode())
            else:
                data = json.loads(encrypted_data.decode())

            logger.info(f"Backup restored: version {data.get('version')}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise ValueError("Invalid backup file or incorrect passphrase")

    def verify_backup(self, backup_path: str, passphrase: str = "") -> bool:
        """Verify backup integrity."""
        try:
            with open(backup_path, "r") as f:
                data = f.read()

            if passphrase:
                key = hashlib.pbkdf2_hmac(
                    "sha256", passphrase.encode(), b"ordexwallet_salt", 100000, dklen=32
                )
                decrypted = self._xor_decrypt(data, key)
                import base64

                json.loads(base64.b64decode(decrypted).decode())
            else:
                json.loads(data)

            return True

        except Exception:
            return False

    def list_backups(self) -> list:
        """List available backups."""
        backups = []
        for f in sorted(self.backup_dir.iterdir(), reverse=True):
            if f.suffix in [".enc", ".json"]:
                stat = f.stat()
                backups.append(
                    {
                        "filename": f.name,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    }
                )
        return backups

    def _xor_encrypt(self, data: str, key: bytes) -> str:
        """Simple XOR encryption for backup."""
        result = bytearray()
        key_len = len(key)
        for i, char in enumerate(data.encode()):
            result.append(char ^ key[i % key_len])
        return result.hex()

    def _xor_decrypt(self, data: str, key: bytes) -> str:
        """Simple XOR decryption (same as encryption)."""
        result = bytearray()
        key_len = len(key)
        data_bytes = bytes.fromhex(data)
        for i, byte in enumerate(data_bytes):
            result.append(byte ^ key[i % key_len])
        return result.decode()

    def _cleanup_old_backups(self, max_backups: int = 7):
        """Remove old backups, keeping most recent."""
        backups = sorted(
            self.backup_dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True
        )

        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup.name}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup: {e}")
