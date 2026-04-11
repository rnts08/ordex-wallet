import os
import logging
from dataclasses import dataclass, field
from urllib.parse import urlparse
from typing import List, Optional


logger = logging.getLogger("ordex_web_wallet.config")


class ConfigError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Configuration errors: {'; '.join(errors)}")


@dataclass
class Config:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://webwallet:password@localhost:5432/webwallet"
    )
    OXRPC_URL: str = os.getenv("OXRPC_URL", "http://localhost:5332")
    OGRPC_URL: str = os.getenv("OGRPC_URL", "http://localhost:5333")
    RPC_USER: str = os.getenv("RPC_USER", "ordex")
    RPC_PASS: str = os.getenv("RPC_PASS", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    SESSION_DURATION: int = int(os.getenv("SESSION_DURATION", "86400"))
    DEBUG: bool = os.getenv("FLASK_ENV", "production") == "development"

    required_env_vars: List[str] = field(
        default_factory=lambda: ["DATABASE_URL", "RPC_PASS"]
    )
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        self._validate()

    def _validate(self) -> None:
        skip_validation = os.getenv("SKIP_CONFIG_VALIDATION", "").lower() == "true"

        self.validation_errors = []

        if skip_validation:
            if not self.RPC_PASS:
                self.validation_errors.append("RPC_PASS must be set")
            if (
                not self.DATABASE_URL
                or self.DATABASE_URL
                == "postgresql://webwallet:password@localhost:5432/webwallet"
            ):
                self.validation_errors.append(
                    "DATABASE_URL must be configured with secure password"
                )
            db_pass = self._get_db_password()
            if db_pass == "password" or db_pass == "your_secure_password_here":
                self.validation_errors.append(
                    "DATABASE_URL contains default/insecure password"
                )

            if not self.SECRET_KEY:
                import secrets

                self.SECRET_KEY = secrets.token_urlsafe(32)
                logger.warning("SECRET_KEY auto-generated")

            if self.validation_errors:
                logger.warning(
                    f"Config validation issues (ignored): {self.validation_errors}"
                )
                self.validation_errors = []
            return

        if not self.RPC_PASS:
            self.validation_errors.append("RPC_PASS must be set")

        if (
            not self.DATABASE_URL
            or self.DATABASE_URL
            == "postgresql://webwallet:password@localhost:5432/webwallet"
        ):
            self.validation_errors.append(
                "DATABASE_URL must be configured with secure password"
            )

        db_pass = self._get_db_password()
        if db_pass == "password" or db_pass == "your_secure_password_here":
            self.validation_errors.append(
                "DATABASE_URL contains default/insecure password"
            )

        if not self.SECRET_KEY:
            import secrets

            self.SECRET_KEY = secrets.token_urlsafe(32)
            logger.warning("SECRET_KEY auto-generated (consider setting explicitly)")

        if self.validation_errors:
            logger.error(f"Configuration validation failed: {self.validation_errors}")
            raise ConfigError(self.validation_errors)

        logger.info("Configuration validated successfully")

    def _get_db_password(self) -> Optional[str]:
        try:
            parsed = urlparse(self.DATABASE_URL)
            return parsed.password
        except Exception:
            return None

    def validate_runtime(self) -> List[str]:
        errors = []

        try:
            from ordex_web_wallet.database import DATABASE

            result = DATABASE.execute_one("SELECT 1")
            if result is None:
                errors.append("Database connection failed")
        except Exception as e:
            errors.append(f"Database unavailable: {str(e)}")

        try:
            from ordex_web_wallet.rpc import daemon_manager

            daemon_manager.get_blockchain_info("ordexcoin")
        except Exception as e:
            errors.append(f"OrdexCoin daemon unavailable: {str(e)}")

        try:
            from ordex_web_wallet.rpc import daemon_manager

            daemon_manager.get_blockchain_info("ordexgold")
        except Exception as e:
            errors.append(f"OrdexGold daemon unavailable: {str(e)}")

        return errors


import uuid


def get_config() -> Config:
    """Get config."""
    return Config()


def _get_config_safe():
    """Get config without failing on validation errors."""
    skip = os.getenv("SKIP_CONFIG_VALIDATION", "").lower() == "true"
    cfg = Config()
    if cfg.validation_errors and not skip:
        raise ConfigError(cfg.validation_errors)
    return cfg


config = _get_config_safe()


def get_database_config():
    cfg = config
    if cfg is None:
        return {
            "host": "localhost",
            "port": 5432,
            "database": "webwallet",
            "user": "webwallet",
            "password": "",
        }
    parsed = urlparse(cfg.DATABASE_URL)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
    }
    parsed = urlparse(cfg.DATABASE_URL)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
    }
