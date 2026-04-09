import os
from dataclasses import dataclass
from urllib.parse import urlparse


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

    def __post_init__(self):
        if not self.SECRET_KEY:
            import secrets

            self.SECRET_KEY = secrets.token_urlsafe(32)
        if not self.RPC_PASS:
            raise ValueError("RPC_PASS must be set")


config = Config()


def get_database_config():
    parsed = urlparse(config.DATABASE_URL)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
    }
