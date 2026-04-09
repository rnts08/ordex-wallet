"""
Config Auto-Generation Module for OrdexWallet.

Generates secure RPC credentials and configuration files on first startup.
"""

import os
import json
import secrets
import string
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigGenerator:
    """Handles automatic generation of configuration files with secure credentials."""

    DEFAULT_RPC_PORTS = {
        "ordexcoind": int(os.environ.get("ORDEXCOIND_RPC_PORT", "25173")),
        "ordexgoldd": int(os.environ.get("ORDEXGOLDD_RPC_PORT", "25466")),
    }

    DEFAULT_P2P_PORTS = {"ordexcoind": 9333, "ordexgoldd": 9334}

    DEFAULT_P2P_PORTS = {
        "ordexcoind": int(os.environ.get("ORDEXCOIND_P2P_PORT", "9333")),
        "ordexgoldd": int(os.environ.get("ORDEXGOLDD_P2P_PORT", "9334")),
    }

    def __init__(self, config_dir: str, data_dir: str):
        """
        Initialize the config generator.

        Args:
            config_dir: Directory for config files
            data_dir: Directory for application data
        """
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def is_first_startup(self) -> bool:
        """Check if this is the first startup (no config exists)."""
        required_files = ["ordexcoind.conf", "ordexgoldd.conf", "config.json"]
        return not all((self.config_dir / f).exists() for f in required_files)

    @staticmethod
    def generate_secure_password(length: int = 32) -> str:
        """Generate a cryptographically secure password using token_urlsafe for better entropy."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_rpc_credentials() -> Dict[str, str]:
        """Generate RPC user and password credentials."""
        return {
            "rpcuser": "ordexuser_" + secrets.token_hex(8),
            "rpcpassword": ConfigGenerator.generate_secure_password(32),
        }

    def _generate_daemon_config(self, daemon_name: str) -> Dict[str, Any]:
        """Generate config for a specific daemon."""
        creds = self.generate_rpc_credentials()
        rpc_port = self.DEFAULT_RPC_PORTS.get(daemon_name, 8332)
        p2p_port = self.DEFAULT_P2P_PORTS.get(daemon_name, 8333)

        datadir = (
            "/data/blockchain/ordexcoin"
            if daemon_name == "ordexcoind"
            else "/data/blockchain/ordexgold"
        )

        return {
            "datadir": datadir,
            "rpcuser": creds["rpcuser"],
            "rpcpassword": creds["rpcpassword"],
            "rpcport": rpc_port,
            "rpcbind": f"127.0.0.1:{rpc_port}",
            "rpcallowip": "127.0.0.1",
            "server": 1,
            "daemon": 1,
            "listen": 1,
            "p2pport": p2p_port,
            "txindex": 1,
            "dbcache": 512,
            "maxconnections": 16,
            "maxmempool": 300,
            "minchainfreespace": 200,
            "prune": 0,
            "printtoconsole": 0,
            "logips": 1,
            "blockfilterindex": 1,
            "disabledprune": 1,
        }

    def _generate_app_config(
        self, ordexcoin_creds: Dict, ordexgold_creds: Dict
    ) -> Dict[str, Any]:
        """Generate main application config."""
        return {
            "version": "1.0.0",
            "daemons": {
                "ordexcoind": {
                    "host": "localhost",
                    "port": self.DEFAULT_RPC_PORTS["ordexcoind"],
                    "username": ordexcoin_creds["rpcuser"],
                    "password": ordexcoin_creds["rpcpassword"],
                    "conf_file": "ordexcoin.conf",
                },
                "ordexgoldd": {
                    "host": "localhost",
                    "port": self.DEFAULT_RPC_PORTS["ordexgoldd"],
                    "username": ordexgold_creds["rpcuser"],
                    "password": ordexgold_creds["rpcpassword"],
                    "conf_file": "ordexgold.conf",
                },
            },
            "wallet": {
                "encrypt_backups": True,
                "backup_frequency_hours": 24,
                "max_backups": 7,
                "passphrase_required": False,
            },
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False,
                "secret_key": self.generate_secure_password(48),
            },
            "market": {
                "enabled": True,
                "default_exchange": "nestex",
                "update_interval_minutes": 5,
                "fallback_mode": True,
            },
            "system": {
                "stats_interval_seconds": 30,
                "log_retention_days": 30,
                "max_log_size_mb": 100,
            },
            "daemon_defaults": {
                "dbcache": 512,
                "maxconnections": 16,
                "prune": 0,
                "maxmempool": 300,
                "minchainfreespace": 200,
                "blocksonly": False,
                "txindex": True,
            },
        }

    def _write_daemon_config(self, daemon_name: str, config: Dict[str, Any]) -> Path:
        """Write daemon config file in bitcoind-compatible format."""
        config_path = self.config_dir / f"{daemon_name}.conf"

        with open(config_path, "w") as f:
            for key, value in config.items():
                if isinstance(value, bool):
                    f.write(f"{key}={1 if value else 0}\n")
                elif isinstance(value, int) and value == 0 and key == "prune":
                    f.write(f"{key}=0\n")
                else:
                    f.write(f"{key}={value}\n")

        os.chmod(config_path, 0o600)
        logger.info(f"Generated config for {daemon_name} at {config_path}")
        return config_path

    def _write_app_config(self, config: Dict[str, Any]) -> Path:
        """Write main application config as JSON."""
        config_path = self.config_dir / "config.json"

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        os.chmod(config_path, 0o600)
        logger.info(f"Generated app config at {config_path}")
        return config_path

    def generate_all_configs(self) -> Dict[str, Path]:
        """
        Generate all configuration files.

        Returns:
            Dict mapping config names to file paths
        """
        if not self.is_first_startup():
            logger.info("Configs already exist, skipping generation")
            return {}

        logger.info("First startup detected, generating configs...")

        ordexcoin_config = self._generate_daemon_config("ordexcoind")
        ordexgold_config = self._generate_daemon_config("ordexgoldd")

        self._write_daemon_config("ordexcoind", ordexcoin_config)
        self._write_daemon_config("ordexgoldd", ordexgold_config)

        ordexcoin_creds = {
            "rpcuser": ordexcoin_config["rpcuser"],
            "rpcpassword": ordexcoin_config["rpcpassword"],
        }
        ordexgold_creds = {
            "rpcuser": ordexgold_config["rpcuser"],
            "rpcpassword": ordexgold_config["rpcpassword"],
        }

        app_config = self._generate_app_config(ordexcoin_creds, ordexgold_creds)
        self._write_app_config(app_config)

        return {
            "ordexcoin.conf": self.config_dir / "ordexcoin.conf",
            "ordexgold.conf": self.config_dir / "ordexgold.conf",
            "config.json": self.config_dir / "config.json",
        }

    def load_config(self) -> Dict[str, Any]:
        """Load existing application config."""
        config_path = self.config_dir / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            return json.load(f)

    def update_daemon_config(self, daemon_name: str, updates: Dict[str, Any]) -> None:
        """Update daemon config with new values."""
        config_path = self.config_dir / f"{daemon_name}.conf"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        config = {}
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    config[key] = value

        config.update(updates)

        with open(config_path, "w") as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")

        os.chmod(config_path, 0o600)
        logger.info(f"Updated config for {daemon_name}")

    def get_daemon_config(self, daemon_name: str) -> Dict[str, Any]:
        """Read daemon config as dict."""
        config_path = self.config_dir / f"{daemon_name}.conf"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        config = {}
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    try:
                        config[key] = int(value)
                    except ValueError:
                        config[key] = value

        return config
