#!/usr/bin/env python3
"""Initialize admin user for Ordex Web Wallet."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def init_admin(username: str, password: str, email: str = None):
    import bcrypt
    from ordex_web_wallet.database import (
        get_user_by_username,
        create_user,
        init_database,
    )

    init_database()

    existing = get_user_by_username(username)
    if existing:
        print(f"Admin user '{username}' already exists")
        return

    email = email or f"admin@{username}.local"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = create_user(username, email, password_hash, is_admin=True)
    print(f"Admin user '{username}' created with ID: {user['id']}")

    from ordex_web_wallet.rpc import daemon_manager

    try:
        daemon_manager.create_user_wallet(user["id"], "ordexcoin", password)
        daemon_manager.create_user_wallet(user["id"], "ordexgold", password)
        print("Admin wallets created")
    except Exception as e:
        print(f"Warning: Could not create wallets: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize admin user")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--email", help="Admin email")

    args = parser.parse_args()
    init_admin(args.username, args.password, args.email)
