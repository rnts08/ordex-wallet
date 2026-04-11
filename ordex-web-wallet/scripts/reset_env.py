#!/usr/bin/env python3
"""
Reset Ordex Web Wallet environment.

Removes all users (except creates fresh walletadmin), cleans wallet files,
and reinitializes the database schema.

Usage:
    python reset_env.py              # Interactive mode
    python reset_env.py --force     # Skip confirmation
    python reset_env.py --keep-db   # Keep database, only reset wallets
"""

import os
import sys
import shutil
import argparse
import subprocess

os.environ["SKIP_CONFIG_VALIDATION"] = "true"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import bcrypt
from ordex_web_wallet.config import config
from ordex_web_wallet.database import (
    init_database,
    hash_password,
    create_user,
    get_user_by_username,
    DATABASE,
)

WALLET_DATA_DIR = os.getenv("WALLET_DATA_DIR", "/data")


def get_docker_db_url() -> str:
    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "ordex-web-wallet-postgres",
                "--format",
                "{{.NetworkSettings.Networks.docker_webwallet_network.IPAddress}}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        ip = result.stdout.strip()
        if ip:
            db_pass = os.getenv("DB_PASSWORD", "4w3s0m3Passw0rd")
            return f"postgresql://webwallet:{db_pass}@{ip}:5432/webwallet"
    except:
        pass
    return os.getenv(
        "DATABASE_URL",
        "postgresql://webwallet:4w3s0m3Passw0rd@localhost:5432/webwallet",
    )


def truncate_tables():
    """Delete all data from tables in correct order (respecting FK constraints)."""
    print("Truncating database tables...")

    tables = [
        "transactions",
        "address_book",
        "messages",
        "audit_log",
        "sessions",
        "user_wallets",
        "users",
    ]

    for table in tables:
        try:
            DATABASE.execute_write(f"TRUNCATE TABLE {table} CASCADE")
            print(f"  - Truncated {table}")
        except Exception as e:
            print(f"  - Warning: {table}: {e}")

    print("Database truncated.")


def reset_admin():
    """Ensure walletadmin exists with password 'changeme26'."""
    print("Creating admin user...")

    pw_hash = hash_password("changeme26")
    admin = get_user_by_username("walletadmin")

    if admin:
        DATABASE.execute_write(
            "UPDATE users SET password_hash = %s, is_active = TRUE, is_admin = TRUE "
            "WHERE username = %s",
            (pw_hash, "walletadmin"),
        )
        print("  - Updated existing walletadmin user")
    else:
        create_user("walletadmin", "admin@ordex.local", pw_hash, is_admin=True)
        print("  - Created new walletadmin user")

    print("Admin user 'walletadmin' ready with password 'changeme26'")


def reset_wallets():
    """Remove wallet directories to force fresh wallet creation."""
    print("Cleaning wallet files...")

    wallet_dir = os.path.join(WALLET_DATA_DIR, "wallets")

    try:
        if os.path.exists(wallet_dir):
            shutil.rmtree(wallet_dir)
            print(f"  - Removed {wallet_dir}")
        else:
            print(f"  - Wallet directory not found at {wallet_dir}")
    except Exception as e:
        print(f"  - Warning: Could not remove wallet dir: {e}")

    for chain in ["ordexcoin", "ordexgold"]:
        lock_dir = os.path.join(WALLET_DATA_DIR, f"{chain}.lock")
        try:
            if os.path.exists(lock_dir):
                os.remove(lock_dir)
                print(f"  - Removed {lock_dir}")
        except Exception as e:
            print(f"  - Warning: Could not remove {lock_dir}: {e}")

    print("Wallet files cleaned.")


def reset_env(keep_db: bool = False, force: bool = False):
    """Main reset function."""
    if not force:
        confirm = input(
            "This will DESTROY all user data and wallet files. Continue? (y/N): "
        )
        if confirm.lower() != "y":
            print("Reset aborted.")
            sys.exit(0)

    db_url = get_docker_db_url()
    os.environ["DATABASE_URL"] = db_url
    os.environ["RPC_PASS"] = os.getenv("RPC_PASSWORD", "ordexRPC123")

    import importlib
    import ordex_web_wallet.config
    import ordex_web_wallet.database

    importlib.reload(ordex_web_wallet.config)
    importlib.reload(ordex_web_wallet.database)

    from ordex_web_wallet.database import (
        init_database,
        DATABASE,
    )
    from ordex_web_wallet.database import hash_password, get_user_by_username

    def do_truncate():
        """Local wrapper for truncate."""
        print("Truncating database tables...")
        tables = [
            "transactions",
            "address_book",
            "messages",
            "audit_log",
            "sessions",
            "user_wallets",
            "users",
        ]
        for table in tables:
            try:
                DATABASE.execute_write(f"TRUNCATE TABLE {table} CASCADE")
                print(f"  - Truncated {table}")
            except Exception as e:
                print(f"  - Warning: {table}: {e}")
        print("Database truncated.")

    print("\n=== Ordex Web Wallet Environment Reset ===\n")
    print(f"Using database: {db_url.replace(':***@', ':***@')}")

    try:
        if not keep_db:
            do_truncate()
            init_database()
        else:
            print("Skipping database reset (--keep-db mode)")

        reset_admin()

        reset_wallets()

        print("\n=== Reset Complete ===")
        print("Login with: walletadmin / changeme26")
        print("IMPORTANT: Change password immediately in production!")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset Ordex Web Wallet environment")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Keep database, only reset wallets and admin",
    )
    args = parser.parse_args()

    reset_env(keep_db=args.keep_db, force=args.force)
