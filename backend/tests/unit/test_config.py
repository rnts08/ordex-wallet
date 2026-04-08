"""
Unit tests for ConfigGenerator.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from config import ConfigGenerator


class TestConfigGenerator(unittest.TestCase):
    """Test cases for ConfigGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.data_dir = Path(self.temp_dir) / "data"
        self.config_dir.mkdir(parents=True)
        self.data_dir.mkdir(parents=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_first_startup_no_configs(self):
        """Test first startup detection when no configs exist."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        self.assertTrue(generator.is_first_startup())

    def test_is_first_startup_partial_configs(self):
        """Test first startup detection with partial configs."""
        (self.config_dir / "ordexcoin.conf").touch()
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        self.assertTrue(generator.is_first_startup())

    def test_is_first_startup_all_configs(self):
        """Test first startup detection when all configs exist."""
        (self.config_dir / "ordexcoind.conf").touch()
        (self.config_dir / "ordexgoldd.conf").touch()
        (self.config_dir / "config.json").write_text("{}")
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        self.assertFalse(generator.is_first_startup())

    def test_generate_secure_password_length(self):
        """Test password generation length."""
        password = ConfigGenerator.generate_secure_password(32)
        self.assertEqual(len(password), 32)

    def test_generate_secure_password_unique(self):
        """Test that generated passwords are unique."""
        passwords = [ConfigGenerator.generate_secure_password(32) for _ in range(100)]
        self.assertEqual(len(set(passwords)), 100)

    def test_generate_rpc_credentials(self):
        """Test RPC credentials generation."""
        creds = ConfigGenerator.generate_rpc_credentials()
        self.assertIn("rpcuser", creds)
        self.assertIn("rpcpassword", creds)
        self.assertTrue(creds["rpcuser"].startswith("ordexuser_"))
        self.assertEqual(len(creds["rpcpassword"]), 32)

    def test_generate_daemon_config_ordexcoind(self):
        """Test daemon config generation for ordexcoind."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        config = generator._generate_daemon_config("ordexcoind")

        self.assertEqual(config["rpcport"], 25173)
        self.assertEqual(config["rpcbind"], "127.0.0.1:25173")
        self.assertEqual(config["p2pport"], 9333)
        self.assertEqual(config["txindex"], 1)
        self.assertEqual(config["dbcache"], 512)
        self.assertEqual(config["maxconnections"], 16)

    def test_generate_daemon_config_ordexgoldd(self):
        """Test daemon config generation for ordexgoldd."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        config = generator._generate_daemon_config("ordexgoldd")

        self.assertEqual(config["rpcport"], 25466)
        self.assertEqual(config["rpcbind"], "127.0.0.1:25466")
        self.assertEqual(config["p2pport"], 9334)

    def test_generate_app_config(self):
        """Test application config generation."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))

        ordexcoin_creds = {"rpcuser": "user1", "rpcpassword": "pass1"}
        ordexgold_creds = {"rpcuser": "user2", "rpcpassword": "pass2"}

        config = generator._generate_app_config(ordexcoin_creds, ordexgold_creds)

        self.assertEqual(config["version"], "1.0.0")
        self.assertEqual(config["daemons"]["ordexcoind"]["port"], 25173)
        self.assertEqual(config["daemons"]["ordexgoldd"]["port"], 25466)
        self.assertEqual(config["wallet"]["backup_frequency_hours"], 24)
        self.assertEqual(config["wallet"]["max_backups"], 7)
        self.assertEqual(config["api"]["port"], 5000)
        self.assertEqual(config["daemon_defaults"]["dbcache"], 512)

    def test_write_daemon_config(self):
        """Test writing daemon config to file."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        config = {"rpcuser": "testuser", "rpcpassword": "testpass", "rpcport": 25173}

        path = generator._write_daemon_config("ordexcoind", config)

        self.assertTrue(path.exists())
        self.assertEqual(path.name, "ordexcoind.conf")

        stat = os.stat(path)
        self.assertEqual(stat.st_mode & 0o777, 0o600)

    def test_write_app_config(self):
        """Test writing application config to file."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        config = {"version": "1.0.0", "api": {"port": 5000}}

        path = generator._write_app_config(config)

        self.assertTrue(path.exists())
        self.assertEqual(path.name, "config.json")

        with open(path, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["version"], "1.0.0")

    def test_generate_all_configs(self):
        """Test full config generation on first startup."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))

        result = generator.generate_all_configs()

        self.assertEqual(len(result), 3)
        self.assertTrue((self.config_dir / "ordexcoind.conf").exists())
        self.assertTrue((self.config_dir / "ordexgoldd.conf").exists())
        self.assertTrue((self.config_dir / "config.json").exists())

        loaded = generator.load_config()
        self.assertEqual(loaded["version"], "1.0.0")

    def test_generate_all_configs_skips_existing(self):
        """Test that generation is skipped when configs exist."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))

        self.assertTrue(generator.is_first_startup())

        result1 = generator.generate_all_configs()
        self.assertEqual(len(result1), 3)

        self.assertFalse(generator.is_first_startup())

        result2 = generator.generate_all_configs()
        self.assertEqual(len(result2), 0)

    def test_update_daemon_config(self):
        """Test updating daemon config."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        generator.generate_all_configs()

        generator.update_daemon_config(
            "ordexcoind", {"dbcache": 1024, "maxconnections": 32}
        )

        config = generator.get_daemon_config("ordexcoind")
        self.assertEqual(config["dbcache"], 1024)
        self.assertEqual(config["maxconnections"], 32)

    def test_get_daemon_config(self):
        """Test reading daemon config."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))
        generator.generate_all_configs()

        config = generator.get_daemon_config("ordexcoind")

        self.assertIn("rpcuser", config)
        self.assertIn("rpcpassword", config)
        self.assertIn("rpcport", config)


class TestConfigGeneratorIntegration(unittest.TestCase):
    """Integration tests for ConfigGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.data_dir = Path(self.temp_dir) / "data"
        self.config_dir.mkdir(parents=True)
        self.data_dir.mkdir(parents=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_config_lifecycle(self):
        """Test complete config generation and loading lifecycle."""
        generator = ConfigGenerator(str(self.config_dir), str(self.data_dir))

        self.assertTrue(generator.is_first_startup())

        generator.generate_all_configs()

        self.assertFalse(generator.is_first_startup())

        loaded = generator.load_config()

        self.assertEqual(loaded["daemons"]["ordexcoind"]["port"], 25173)
        self.assertEqual(loaded["daemons"]["ordexgoldd"]["port"], 25466)

        ordexcoin_conf = generator.get_daemon_config("ordexcoind")
        self.assertEqual(ordexcoin_conf["rpcport"], 25173)

        ordexgold_conf = generator.get_daemon_config("ordexgoldd")
        self.assertEqual(ordexgold_conf["rpcport"], 25466)


if __name__ == "__main__":
    unittest.main()
