"""
SQLite Database Module for OrdexWallet.

Provides database operations for wallet data, transactions, and settings.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for OrdexWallet."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_connection()
        self._init_tables()
        logger.info(f"Database initialized at {db_path}")

    def _ensure_db_dir(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _init_connection(self):
        """Initialize database connection with optimizations."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor."""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Database error: {e}")
            raise e

    def is_first_startup(self) -> bool:
        """Check if this is the first startup (database needs initialization)."""
        with self.get_cursor() as cursor:
            # Check if schema version is set
            cursor.execute("SELECT value FROM settings WHERE key = 'schema_version'")
            row = cursor.fetchone()
            if row is None:
                return True
            return False

    def initialize(self) -> bool:
        """Initialize or migrate database. Returns True if initialization occurred."""
        with self.get_cursor() as cursor:
            # Check current schema version
            cursor.execute("SELECT value FROM settings WHERE key = 'schema_version'")
            row = cursor.fetchone()

            if row is None:
                # Fresh database - run initialization
                logger.info("Running database initialization...")
                self._init_tables()

                # Set schema version
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ("schema_version", str(self.SCHEMA_VERSION)),
                )

                # Set initialized timestamp
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ("initialized_at", datetime.now().isoformat()),
                )

                logger.info("Database initialization complete")
                return True
            else:
                current_version = int(row["value"])
                if current_version < self.SCHEMA_VERSION:
                    logger.info(
                        f"Running database migration from v{current_version} to v{self.SCHEMA_VERSION}"
                    )
                    # Future: run migrations here
                    cursor.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        ("schema_version", str(self.SCHEMA_VERSION)),
                    )
                    return True

        return False

    def _init_tables(self):
        """Initialize database tables (idempotent)."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallet_meta (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    has_wallet INTEGER DEFAULT 0,
                    created_at TEXT,
                    last_backup TEXT,
                    backup_passphrase_hash TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    txid TEXT UNIQUE,
                    network TEXT NOT NULL,
                    address TEXT,
                    amount REAL,
                    fee REAL,
                    confirmations INTEGER DEFAULT 0,
                    category TEXT,
                    blockhash TEXT,
                    blocktime INTEGER,
                    time INTEGER,
                    timereceived INTEGER,
                    comment TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS addresses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE,
                    network TEXT NOT NULL,
                    label TEXT,
                    account TEXT DEFAULT '',
                    is_change INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT,
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_network 
                ON transactions(network)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_address 
                ON transactions(address)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_addresses_network 
                ON addresses(network)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_log_created 
                ON audit_log(created_at)
            """)

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value."""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
            """,
                (key, value, value),
            )

    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT key, value FROM settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    def has_wallet(self) -> bool:
        """Check if wallet exists."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT has_wallet FROM wallet_meta WHERE id = 1")
            row = cursor.fetchone()
            return row["has_wallet"] == 1 if row else False

    def create_wallet(self, passphrase_hash: Optional[str] = None) -> None:
        """Create wallet metadata."""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT OR REPLACE INTO wallet_meta 
                (id, has_wallet, created_at, backup_passphrase_hash)
                VALUES (1, 1, CURRENT_TIMESTAMP, ?)
            """,
                (passphrase_hash,),
            )

    def delete_wallet(self) -> None:
        """Delete wallet metadata."""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM wallet_meta WHERE id = 1")
            cursor.execute("DELETE FROM addresses")
            cursor.execute("DELETE FROM transactions WHERE category = 'move'")

    def get_wallet_meta(self) -> Optional[Dict[str, Any]]:
        """Get wallet metadata."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM wallet_meta WHERE id = 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_last_backup(self) -> None:
        """Update last backup timestamp."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE wallet_meta SET last_backup = CURRENT_TIMESTAMP WHERE id = 1
            """)

    def add_address(
        self,
        address: str,
        network: str,
        label: str = "",
        account: str = "",
        is_change: bool = False,
    ) -> None:
        """Add an address to the database."""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT OR IGNORE INTO addresses (address, network, label, account, is_change)
                VALUES (?, ?, ?, ?, ?)
            """,
                (address, network, label, account, 1 if is_change else 0),
            )

    def get_addresses(
        self, network: Optional[str] = None, is_change: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get addresses from database."""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM addresses WHERE 1=1"
            params = []
            if network:
                query += " AND network = ?"
                params.append(network)
            if is_change is not None:
                query += " AND is_change = ?"
                params.append(1 if is_change else 0)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def add_transaction(
        self,
        txid: str,
        network: str,
        address: str,
        amount: float,
        fee: float,
        category: str,
        confirmations: int = 0,
        blockhash: Optional[str] = None,
        blocktime: Optional[int] = None,
        time: Optional[int] = None,
        comment: str = "",
    ) -> None:
        """Add a transaction to the database."""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT OR REPLACE INTO transactions 
                (txid, network, address, amount, fee, category, confirmations, 
                 blockhash, blocktime, time, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    txid,
                    network,
                    address,
                    amount,
                    fee,
                    category,
                    confirmations,
                    blockhash,
                    blocktime,
                    time,
                    comment,
                ),
            )

    def get_transactions(
        self,
        network: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get transactions from database."""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM transactions WHERE 1=1"
            params = []
            if network:
                query += " AND network = ?"
                params.append(network)
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_transaction(self, txid: str) -> Optional[Dict[str, Any]]:
        """Get a specific transaction."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM transactions WHERE txid = ?", (txid,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_transaction_confirmations(
        self,
        txid: str,
        confirmations: int,
        blockhash: Optional[str] = None,
        blocktime: Optional[int] = None,
    ) -> None:
        """Update transaction confirmations."""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE transactions 
                SET confirmations = ?, blockhash = ?, blocktime = ?
                WHERE txid = ?
            """,
                (confirmations, blockhash, blocktime, txid),
            )

    def add_audit_log(
        self,
        level: str,
        category: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an audit log entry."""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_log (level, category, message, details)
                VALUES (?, ?, ?, ?)
            """,
                (level, category, message, json.dumps(details) if details else None),
            )

    def get_audit_logs(
        self,
        level: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get audit logs."""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            if level:
                query += " AND level = ?"
                params.append(level)
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()


class DatabaseManager:
    """Manages database instances for both networks."""

    def __init__(self, data_dir: str):
        """Initialize database manager."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.main_db = Database(str(self.data_dir / "ordexwallet.db"))

        # Initialize database (idempotent - runs on every start)
        initialized = self.main_db.initialize()
        if initialized:
            logger.info("Database initialized for first time")
        else:
            logger.info("Database already initialized")

        logger.info("DatabaseManager initialized")

    def get_db(self) -> Database:
        """Get main database instance."""
        return self.main_db

    def close(self) -> None:
        """Close all database connections."""
        self.main_db.close()
