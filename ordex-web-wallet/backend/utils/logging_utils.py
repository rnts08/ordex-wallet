import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Any, Dict

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
AUTH_LOG_FILE = os.path.join(LOG_DIR, "auth.log")
WALLET_LOG_FILE = os.path.join(LOG_DIR, "wallet.log")
ADMIN_LOG_FILE = os.path.join(LOG_DIR, "admin.log")
RPC_LOG_FILE = os.path.join(LOG_DIR, "rpc.log")
DB_LOG_FILE = os.path.join(LOG_DIR, "database.log")


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def get_formatter(logger_name: str) -> logging.Formatter:
    return logging.Formatter(
        f"%(asctime)s [%(levelname)s] [{logger_name}] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_file_handler(log_file: str, logger_name: str) -> RotatingFileHandler:
    ensure_log_dir()
    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setFormatter(get_formatter(logger_name))
    return handler


def get_console_handler(logger_name: str) -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setFormatter(get_formatter(logger_name))
    return handler


def get_logger(
    name: str, log_file: str = None, level: int = logging.INFO
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    for h in logger.handlers[:]:
        logger.removeHandler(h)

    logger.addHandler(get_console_handler(name))

    if log_file:
        logger.addHandler(get_file_handler(log_file, name))

    return logger


app_logger = get_logger("app", APP_LOG_FILE)
auth_logger = get_logger("auth", AUTH_LOG_FILE)
wallet_logger = get_logger("wallet", WALLET_LOG_FILE)
admin_logger = get_logger("admin", ADMIN_LOG_FILE)
rpc_logger = get_logger("rpc", RPC_LOG_FILE)
db_logger = get_logger("database", DB_LOG_FILE)


def log_event(
    logger: logging.Logger,
    level: int,
    event_type: str,
    user_id: Optional[int] = None,
    **kwargs: Any,
) -> None:
    data = {"event": event_type}
    if user_id:
        data["user_id"] = user_id
    data.update(kwargs)

    msg = f"{event_type} | user_id={user_id} | " + " | ".join(
        f"{k}={v}" for k, v in kwargs.items()
    )

    logger.log(level, msg)


def log_auth(
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    success: bool = True,
    **kwargs: Any,
) -> None:
    level = logging.INFO if success else logging.WARNING
    msg = f"{action} | "
    if username:
        msg += f"username={username} | "
    msg += f"user_id={user_id} | success={success}"
    if kwargs:
        msg += " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())

    if success:
        auth_logger.info(msg)
    else:
        auth_logger.warning(msg)


def log_wallet(
    action: str, user_id: int, chain: str, success: bool = True, **kwargs: Any
) -> None:
    level = logging.INFO if success else logging.WARNING
    msg = f"{action} | user_id={user_id} | chain={chain}"
    if kwargs:
        msg += " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())

    if success:
        wallet_logger.info(msg)
    else:
        wallet_logger.warning(msg)


def log_admin(
    action: str,
    admin_id: int,
    target_user_id: Optional[int] = None,
    success: bool = True,
    **kwargs: Any,
) -> None:
    level = logging.INFO if success else logging.WARNING
    msg = f"{action} | admin_id={admin_id}"
    if target_user_id:
        msg += f" | target_user_id={target_user_id}"
    if kwargs:
        msg += " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())

    if success:
        admin_logger.info(msg)
    else:
        admin_logger.warning(msg)


def log_rpc(
    method: str,
    chain: str,
    success: bool = True,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
    **kwargs: Any,
) -> None:
    if success:
        msg = f"{method} | chain={chain}"
        if duration_ms:
            msg += f" | duration_ms={duration_ms:.2f}"
        if kwargs:
            msg += " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
        rpc_logger.info(msg)
    else:
        msg = f"{method} | chain={chain} | error={error}"
        if duration_ms:
            msg += f" | duration_ms={duration_ms:.2f}"
        rpc_logger.warning(msg)


def log_db(
    operation: str,
    success: bool = True,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
    **kwargs: Any,
) -> None:
    if success:
        msg = f"{operation}"
        if duration_ms:
            msg += f" | duration_ms={duration_ms:.2f}"
        if kwargs:
            msg += " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
        db_logger.info(msg)
    else:
        msg = f"{operation} | error={error}"
        if duration_ms:
            msg += f" | duration_ms={duration_ms:.2f}"
        db_logger.warning(msg)


def log_app(level: int, message: str, **kwargs: Any) -> None:
    msg = message
    if kwargs:
        msg += " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
    app_logger.log(level, msg)
