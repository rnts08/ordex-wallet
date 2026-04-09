import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

SCHEMA_VERSION = 1


class Database:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", "postgresql://webwallet:password@localhost:5432/webwallet"
        )

    def get_connection(self):
        from ordex_web_wallet.config import get_database_config

        db_config = get_database_config()
        return psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
            cursor_factory=RealDictCursor,
        )

    @contextmanager
    def cursor(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = None):
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall() if cur.description else None

    def execute_one(self, query: str, params: tuple = None):
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone() if cur.description else None

    def execute_write(self, query: str, params: tuple = None):
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS user_wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chain TEXT NOT NULL CHECK (chain IN ('ordexcoin', 'ordexgold')),
    wallet_name TEXT NOT NULL,
    wallet_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, chain)
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    UNIQUE(user_id, setting_key)
);

CREATE TABLE IF NOT EXISTS address_book (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label TEXT,
    address TEXT NOT NULL,
    chain TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    txid TEXT NOT NULL,
    chain TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('send', 'receive')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_audit (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,
    target_user_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_wallets_user ON user_wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit(created_at);
"""

MIGRATIONS = [
    (1, SCHEMA),
]


def get_schema_version() -> int:
    result = DATABASE.execute_one(
        "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
    )
    return result["version"] if result else 0


def apply_migration(version: int, sql: str):
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for statement in statements:
        DATABASE.execute_write(statement)
    DATABASE.execute_write(
        "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT DO NOTHING",
        (version,),
    )


def run_migrations():
    current_version = get_schema_version()
    for version, sql in MIGRATIONS:
        if version > current_version:
            print(f"Applying migration v{version}...")
            apply_migration(version, sql)
            print(f"Migration v{version} applied")


def init_database():
    run_migrations()
    print("Database initialized")


DATABASE = Database()


def get_user_by_id(user_id: int):
    return DATABASE.execute_one(
        "SELECT id, username, email, is_admin, is_active, created_at, last_login FROM users WHERE id = %s",
        (user_id,),
    )


def get_user_by_username(username: str):
    return DATABASE.execute_one("SELECT * FROM users WHERE username = %s", (username,))


def create_user(username: str, email: str, password_hash: str, is_admin: bool = False):
    return DATABASE.execute_one(
        """INSERT INTO users (username, email, password_hash, is_admin)
           VALUES (%s, %s, %s, %s)
           RETURNING id, username, email, is_admin, is_active""",
        (username, email, password_hash, is_admin),
    )


def create_session(user_id: int, token: str, expires_at: str):
    return DATABASE.execute_one(
        """INSERT INTO sessions (user_id, session_token, expires_at)
           VALUES (%s, %s, %s)
           RETURNING id""",
        (user_id, token, expires_at),
    )


def get_session(token: str):
    return DATABASE.execute_one(
        """SELECT s.*, u.username, u.is_admin 
           FROM sessions s 
           JOIN users u ON u.id = s.user_id 
           WHERE s.session_token = %s AND s.expires_at > CURRENT_TIMESTAMP""",
        (token,),
    )


def delete_session(token: str):
    DATABASE.execute_write("DELETE FROM sessions WHERE session_token = %s", (token,))


def clean_expired_sessions():
    DATABASE.execute_write("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")


def get_user_wallets(user_id: int):
    return DATABASE.execute("SELECT * FROM user_wallets WHERE user_id = %s", (user_id,))


def create_user_wallet(
    user_id: int, chain: str, wallet_name: str, wallet_address: str = None
):
    return DATABASE.execute_one(
        """INSERT INTO user_wallets (user_id, chain, wallet_name, wallet_address)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (user_id, chain) DO UPDATE SET wallet_name = EXCLUDED.wallet_name, wallet_address = EXCLUDED.wallet_address
           RETURNING *""",
        (user_id, chain, wallet_name, wallet_address),
    )


def get_user_setting(user_id: int, key: str):
    return DATABASE.execute_one(
        "SELECT setting_value FROM user_settings WHERE user_id = %s AND setting_key = %s",
        (user_id, key),
    )


def set_user_setting(user_id: int, key: str, value: str):
    DATABASE.execute_one(
        """INSERT INTO user_settings (user_id, setting_key, setting_value)
           VALUES (%s, %s, %s)
           ON CONFLICT (user_id, setting_key) 
           DO UPDATE SET setting_value = EXCLUDED.setting_value""",
        (user_id, key, value),
    )


def get_all_users(limit: int = 50, offset: int = 0):
    return DATABASE.execute(
        """SELECT id, username, email, is_admin, is_active, created_at, last_login,
                  (SELECT COUNT(*) FROM user_wallets WHERE user_id = users.id) as wallet_count
           FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s""",
        (limit, offset),
    )


def update_user_status(user_id: int, is_active: bool):
    DATABASE.execute_write(
        "UPDATE users SET is_active = %s WHERE id = %s", (is_active, user_id)
    )


def admin_audit_log(
    admin_user_id: int, action: str, target_user_id: int = None, details: dict = None
):
    DATABASE.execute_write(
        """INSERT INTO admin_audit (admin_user_id, action, target_user_id, details)
           VALUES (%s, %s, %s, %s)""",
        (admin_user_id, action, target_user_id, details),
    )


def get_system_stats():
    stats = DATABASE.execute_one(
        """SELECT 
              (SELECT COUNT(*) FROM users) as total_users,
              (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as active_users,
              (SELECT COUNT(*) FROM users WHERE last_login > NOW() - INTERVAL '24 hours') as active_24h,
              (SELECT COUNT(*) FROM user_wallets) as total_wallets,
              (SELECT COUNT(*) FROM sessions WHERE expires_at > CURRENT_TIMESTAMP) as active_sessions"""
    )
    return dict(stats) if stats else {}


def get_schema_version_db() -> int:
    return get_schema_version()


if __name__ == "__main__":
    init_database()
