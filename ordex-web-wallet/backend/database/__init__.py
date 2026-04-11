import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import bcrypt
import time
from ordex_web_wallet.config import get_database_config
from ordex_web_wallet.utils.logging_utils import log_db

SCHEMA_VERSION = 1


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class Database:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", "postgresql://webwallet:password@localhost:5432/webwallet"
        )

    def get_connection(self):
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
        start = time.time()
        try:
            with self.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchall() if cur.description else None
            duration_ms = (time.time() - start) * 1000
            log_db(
                "execute", success=True, duration_ms=duration_ms, query_type="select"
            )
            return result
        except Exception as e:
            log_db("execute", success=False, error=str(e), query_type="select")
            raise

    def execute_one(self, query: str, params: tuple = None):
        start = time.time()
        try:
            with self.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone() if cur.description else None
            duration_ms = (time.time() - start) * 1000
            log_db(
                "execute_one",
                success=True,
                duration_ms=duration_ms,
                query_type="select",
            )
            return result
        except Exception as e:
            log_db("execute_one", success=False, error=str(e), query_type="select")
            raise

    def execute_write(self, query: str, params: tuple = None):
        start = time.time()
        try:
            with self.cursor() as cur:
                cur.execute(query, params)
                rowcount = cur.rowcount
            duration_ms = (time.time() - start) * 1000
            log_db(
                "execute_write",
                success=True,
                duration_ms=duration_ms,
                query_type="write",
                rowcount=rowcount,
            )
            return rowcount
        except Exception as e:
            log_db("execute_write", success=False, error=str(e), query_type="write")
            raise


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    guid UUID PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret TEXT,
    totp_uris TEXT,
    must_change_password BOOLEAN DEFAULT FALSE,
    opt_out_reminders BOOLEAN DEFAULT FALSE,
    opt_out_notifications BOOLEAN DEFAULT FALSE,
    last_backup TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS user_wallets (
    id SERIAL PRIMARY KEY,
    user_guid UUID NOT NULL REFERENCES users(guid) ON DELETE CASCADE,
    chain TEXT NOT NULL CHECK (chain IN ('ordexcoin', 'ordexgold')),
    wallet_name TEXT NOT NULL,
    wallet_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_guid, chain)
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_guid UUID NOT NULL REFERENCES users(guid) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_guid UUID NOT NULL REFERENCES users(guid) ON DELETE CASCADE,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    UNIQUE(user_guid, setting_key)
);

CREATE TABLE IF NOT EXISTS address_book (
    id SERIAL PRIMARY KEY,
    user_guid UUID NOT NULL REFERENCES users(guid) ON DELETE CASCADE,
    label TEXT,
    address TEXT NOT NULL,
    chain TEXT NOT NULL,
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_guid UUID NOT NULL REFERENCES users(guid) ON DELETE CASCADE,
    txid TEXT NOT NULL,
    chain TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('send', 'receive')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_audit (
    id SERIAL PRIMARY KEY,
    admin_user_guid UUID NOT NULL REFERENCES users(guid),
    action TEXT NOT NULL,
    target_user_guid UUID,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fee_config (
    id SERIAL PRIMARY KEY,
    chain TEXT NOT NULL,
    send_fee_per_kb REAL DEFAULT 0.001,
    receive_fee_percent REAL DEFAULT 0,
    use_auto_fee BOOLEAN DEFAULT TRUE,
    admin_wallet_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chain)
);

CREATE TABLE IF NOT EXISTS user_messages (
    id SERIAL PRIMARY KEY,
    user_guid UUID NOT NULL REFERENCES users(guid) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'reminder',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stake_config (
    id SERIAL PRIMARY KEY,
    chain TEXT NOT NULL,
    apr_percent REAL DEFAULT 5.0,
    intervals TEXT[] DEFAULT ARRAY['1d', '7d', '30d'],
    global_enabled BOOLEAN DEFAULT TRUE,
    auto_stake_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chain)
);

CREATE TABLE IF NOT EXISTS user_stakes (
    id SERIAL PRIMARY KEY,
    user_guid UUID NOT NULL REFERENCES users(guid) ON DELETE CASCADE,
    chain TEXT NOT NULL,
    amount REAL NOT NULL,
    interval TEXT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    accrued_yield REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_wallets_user ON user_wallets(user_guid);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_guid);
CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit(created_at);
"""

MIGRATIONS = [
    (1, SCHEMA),
    (2, "ALTER TABLE users ALTER COLUMN email DROP NOT NULL;"),
    (
        3,
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS guid UUID;
        ALTER TABLE user_wallets ADD COLUMN IF NOT EXISTS user_guid UUID;
    """,
    ),
]


def get_schema_version() -> int:
    try:
        result = DATABASE.execute_one(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
        )
        return result["version"] if result else 0
    except Exception:
        return 0


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
    ensure_admin_user()
    print("Database initialized")


def ensure_admin_user():
    import uuid
    from ordex_web_wallet.rpc import daemon_manager

    admin = get_user_by_username("walletadmin")
    if not admin:
        password_hash = hash_password("changeme26")
        known_guid = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))
        user = DATABASE.execute_one(
            """INSERT INTO users (username, email, password_hash, is_admin, guid)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING *""",
            ("walletadmin", None, password_hash, True, known_guid),
        )
        print("Created default admin user: walletadmin (changeme26)")

        try:
            for chain in ["ordexcoin", "ordexgold"]:
                wallet_name = daemon_manager.create_user_wallet(
                    None, chain, "changeme26", user_guid=known_guid
                )
                daemon_manager.load_wallet(chain, wallet_name)
                addr = daemon_manager.get_or_create_user_address(
                    None, chain, user_guid=known_guid
                )
                create_user_wallet(known_guid, chain, wallet_name, addr)
                print(f"  Created {chain} wallet: {wallet_name}")
        except Exception as e:
            print(f"  Warning: Could not create wallets: {e}")


DATABASE = Database()


def get_user_by_guid(guid: str):
    return DATABASE.execute_one(
        "SELECT * FROM users WHERE guid = %s",
        (guid,),
    )


def get_user_by_username(username: str):
    return DATABASE.execute_one(
        "SELECT * FROM users WHERE username = %s",
        (username,),
    )


def create_user(username: str, email: str, password_hash: str, is_admin: bool = False):
    import uuid

    user_guid = uuid.uuid4()
    return DATABASE.execute_one(
        """INSERT INTO users (username, email, password_hash, is_admin, guid)
           VALUES (%s, %s, %s, %s, %s)
           RETURNING *""",
        (username, email, password_hash, is_admin, str(user_guid)),
    )


def enable_2fa(user_guid: str, secret: str, totp_uri: str):
    DATABASE.execute_write(
        "UPDATE users SET two_factor_enabled = TRUE, two_factor_secret = %s, totp_uris = %s WHERE guid = %s",
        (secret, totp_uri, user_guid),
    )


def disable_2fa(user_guid: str):
    DATABASE.execute_write(
        "UPDATE users SET two_factor_enabled = FALSE, two_factor_secret = NULL, totp_uris = NULL WHERE guid = %s",
        (user_guid,),
    )


def get_2fa_secret(user_guid: str):
    return DATABASE.execute_one(
        "SELECT two_factor_secret, totp_uris FROM users WHERE guid = %s AND two_factor_enabled = TRUE",
        (user_guid,),
    )


def create_session(user_guid: str, token: str, expires_at: str):
    return DATABASE.execute_one(
        """INSERT INTO sessions (user_guid, session_token, expires_at)
           VALUES (%s, %s, %s)
           RETURNING id""",
        (user_guid, token, expires_at),
    )


def get_session(token: str):
    return DATABASE.execute_one(
        """SELECT s.*, u.username, u.is_admin, u.guid as user_guid
           FROM sessions s 
           JOIN users u ON u.guid = s.user_guid 
           WHERE s.session_token = %s AND s.expires_at > CURRENT_TIMESTAMP""",
        (token,),
    )


def delete_session(token: str):
    DATABASE.execute_write("DELETE FROM sessions WHERE session_token = %s", (token,))


def clean_expired_sessions():
    DATABASE.execute_write("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")


def get_user_wallets(user_guid: str):
    return DATABASE.execute(
        "SELECT * FROM user_wallets WHERE user_guid = %s", (user_guid,)
    )


def create_user_wallet(
    user_guid: str,
    chain: str,
    wallet_name: str,
    wallet_address: str = None,
):
    return DATABASE.execute_one(
        """INSERT INTO user_wallets (user_guid, chain, wallet_name, wallet_address)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (user_guid, chain) DO UPDATE SET wallet_name = EXCLUDED.wallet_name, wallet_address = EXCLUDED.wallet_address
           RETURNING *""",
        (user_guid, chain, wallet_name, wallet_address),
    )


def get_user_setting(user_guid: str, key: str):
    return DATABASE.execute_one(
        "SELECT setting_value FROM user_settings WHERE user_guid = %s AND setting_key = %s",
        (user_guid, key),
    )


def set_user_setting(user_guid: str, key: str, value: str):
    DATABASE.execute_one(
        """INSERT INTO user_settings (user_guid, setting_key, setting_value)
           VALUES (%s, %s, %s)
           ON CONFLICT (user_guid, setting_key) 
           DO UPDATE SET setting_value = EXCLUDED.setting_value""",
        (user_guid, key, value),
    )


def get_all_users(
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "DESC",
    search: str = None,
):
    valid_sorts = {"created_at", "username", "last_login", "is_active"}
    if sort_by not in valid_sorts:
        sort_by = "created_at"
    if sort_order not in {"ASC", "DESC"}:
        sort_order = "DESC"

    query = f"""SELECT guid, username, email, is_admin, is_active, created_at, last_login,
                       two_factor_enabled,
                       last_backup, opt_out_reminders, opt_out_notifications,
                       (SELECT COUNT(*) FROM user_wallets WHERE user_guid = users.guid) as wallet_count,
                       (SELECT COUNT(*) FROM user_wallets WHERE user_guid = users.guid AND wallet_address IS NOT NULL) as address_count,
                       (SELECT COALESCE(SUM(amount), 0) FROM transactions t1 WHERE t1.user_guid = users.guid AND t1.type = 'receive') -
                       (SELECT COALESCE(SUM(amount), 0) FROM transactions t2 WHERE t2.user_guid = users.guid AND t2.type = 'send') as total_balance
                FROM users"""
    params = []
    if search:
        query += " WHERE username LIKE %s OR email LIKE %s"
        search_pattern = f"%{search}%"
        params = [search_pattern, search_pattern]
    query += f" ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    return DATABASE.execute(query, tuple(params))


def get_user_transactions(user_guid: str, limit: int = 50, offset: int = 0):
    return DATABASE.execute(
        """SELECT * FROM transactions 
           WHERE user_guid = %s 
           ORDER BY timestamp DESC 
           LIMIT %s OFFSET %s""",
        (user_guid, limit, offset),
    )


def update_user_status(user_guid: str, is_active: bool):
    DATABASE.execute_write(
        "UPDATE users SET is_active = %s WHERE guid = %s", (is_active, user_guid)
    )


def update_password(user_guid: str, password_hash: str):
    DATABASE.execute_write(
        "UPDATE users SET password_hash = %s, must_change_password = FALSE WHERE guid = %s",
        (password_hash, user_guid),
    )


def delete_user(user_guid: str):
    DATABASE.execute_write("DELETE FROM users WHERE guid = %s", (user_guid,))


def admin_audit_log(
    admin_user_guid: str,
    action: str,
    target_user_guid: str = None,
    details: dict = None,
):
    DATABASE.execute_write(
        """INSERT INTO admin_audit (admin_user_guid, action, target_user_guid, details)
           VALUES (%s, %s, %s, %s)""",
        (admin_user_guid, action, target_user_guid, details),
    )


def get_system_stats():
    stats = DATABASE.execute_one(
        """SELECT 
              (SELECT COUNT(*) FROM users) as total_users,
              (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as active_users,
              (SELECT COUNT(*) FROM users WHERE last_login > NOW() - INTERVAL '24 hours') as active_24h,
              (SELECT COUNT(*) FROM user_wallets) as total_wallets,
              (SELECT COUNT(*) FROM sessions WHERE expires_at > CURRENT_TIMESTAMP) as active_sessions,
              (SELECT COUNT(*) FROM transactions) as total_transactions,
              (SELECT COUNT(*) FROM address_book) as total_addresses"""
    )
    return dict(stats) if stats else {}


def get_user_count():
    return DATABASE.execute_one("SELECT COUNT(*) as count FROM users")["count"]


def get_users_paged(
    limit=25, offset=0, sort_by="created_at", sort_order="DESC", search=None
):
    valid_sorts = {"guid", "username", "email", "created_at", "last_login", "is_active"}
    if sort_by not in valid_sorts:
        sort_by = "created_at"
    if sort_order not in {"ASC", "DESC"}:
        sort_order = "DESC"

    query = f"""SELECT guid, username, email, is_admin, is_active, created_at, last_login, two_factor_enabled,
                      last_backup, opt_out_reminders, opt_out_notifications,
                      (SELECT COUNT(*) FROM user_wallets WHERE user_guid = users.guid) as wallet_count,
                      (SELECT COUNT(*) FROM user_wallets WHERE user_guid = users.guid AND wallet_address IS NOT NULL) as address_count,
                      (SELECT COALESCE(SUM(amount), 0) FROM transactions t1 WHERE t1.user_guid = users.guid AND t1.type = 'receive') -
                      (SELECT COALESCE(SUM(amount), 0) FROM transactions t2 WHERE t2.user_guid = users.guid AND t2.type = 'send') as total_balance
                FROM users"""
    params = []
    if search:
        query += " WHERE username LIKE %s OR email LIKE %s"
        search_pattern = f"%{search}%"
        params = [search_pattern, search_pattern]
    query += f" ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    return DATABASE.execute(query, tuple(params))


def get_fee_config(chain: str = None):
    if chain:
        return DATABASE.execute_one(
            "SELECT * FROM fee_config WHERE chain = %s", (chain,)
        )
    return DATABASE.execute("SELECT * FROM fee_config")


def update_fee_config(
    chain: str,
    send_fee: float = None,
    receive_fee: float = None,
    use_auto: bool = None,
    admin_address: str = None,
):
    DATABASE.execute_write(
        """INSERT INTO fee_config (chain, send_fee_per_kb, receive_fee_percent, use_auto_fee, admin_wallet_address, updated_at)
           VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
           ON CONFLICT (chain) DO UPDATE SET
             send_fee_per_kb = COALESCE(%s, fee_config.send_fee_per_kb),
             receive_fee_percent = COALESCE(%s, fee_config.receive_fee_percent),
             use_auto_fee = COALESCE(%s, fee_config.use_auto_fee),
             admin_wallet_address = COALESCE(%s, fee_config.admin_wallet_address),
             updated_at = CURRENT_TIMESTAMP""",
        (
            chain,
            send_fee,
            receive_fee,
            use_auto,
            admin_address,
            send_fee,
            receive_fee,
            use_auto,
            admin_address,
        ),
    )


def create_user_message(
    user_guid: int, title: str, message: str, msg_type: str = "reminder"
):
    DATABASE.execute_write(
        "INSERT INTO user_messages (user_guid, title, message, type) VALUES (%s, %s, %s, %s)",
        (user_guid, title, message, msg_type),
    )


def get_user_messages(user_guid: str, unread_only: bool = False):
    query = "SELECT * FROM user_messages WHERE user_guid = %s"
    params = [user_guid]
    if unread_only:
        query += " AND is_read = FALSE"
    query += " ORDER BY created_at DESC"
    return DATABASE.execute(query, tuple(params))


def mark_message_read(message_id: int):
    DATABASE.execute_write(
        "UPDATE user_messages SET is_read = TRUE WHERE id = %s", (message_id,)
    )


def update_user_backup(user_guid: str):
    DATABASE.execute_write(
        "UPDATE users SET last_backup = CURRENT_TIMESTAMP WHERE id = %s", (user_guid,)
    )


def update_user_settings(
    user_guid: int, opt_out_reminders: bool = None, opt_out_notifications: bool = None
):
    if opt_out_reminders is not None:
        DATABASE.execute_write(
            "UPDATE users SET opt_out_reminders = %s WHERE id = %s",
            (opt_out_reminders, user_guid),
        )
    if opt_out_notifications is not None:
        DATABASE.execute_write(
            "UPDATE users SET opt_out_notifications = %s WHERE id = %s",
            (opt_out_notifications, user_guid),
        )


def get_stake_config(chain: str = None):
    if chain:
        return DATABASE.execute_one(
            "SELECT * FROM stake_config WHERE chain = %s", (chain,)
        )
    return DATABASE.execute("SELECT * FROM stake_config")


def update_stake_config(
    chain: str,
    apr: float = None,
    intervals: list = None,
    enabled: bool = None,
    auto_stake_default: int = None,
):
    DATABASE.execute_write(
        """INSERT INTO stake_config (chain, apr_percent, intervals, global_enabled, auto_stake_default, updated_at)
           VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
           ON CONFLICT (chain) DO UPDATE SET
             apr_percent = COALESCE(%s, stake_config.apr_percent),
             intervals = COALESCE(%s, stake_config.intervals),
             global_enabled = COALESCE(%s, stake_config.global_enabled),
             auto_stake_default = COALESCE(%s, stake_config.auto_stake_default),
             updated_at = CURRENT_TIMESTAMP""",
        (
            chain,
            apr,
            intervals,
            enabled,
            auto_stake_default,
            apr,
            intervals,
            enabled,
            auto_stake_default,
        ),
    )


def get_backup_count():
    result = DATABASE.execute_one(
        "SELECT COUNT(*) as count FROM users WHERE last_backup > CURRENT_TIMESTAMP - INTERVAL '30 days'"
    )
    return result["count"] if result else 0


def get_schema_version_db() -> int:
    return get_schema_version()


if __name__ == "__main__":
    init_database()
