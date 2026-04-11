# Environment Management and Multitenancy Hardening

This plan addresses the need for a clean environment reset script, dual-wallet creation on registration, and ensuring robust multitenant wallet isolation and concurrent access.

## User Review Required

> [!WARNING]
> The reset script will permanently delete all user data from the database and all wallet files from the server's data volumes. Proceed with caution when running this in any environment containing real assets.

> [!IMPORTANT]
> I will be updating the registration flow to automatically create both OrdexCoin and OrdexGold wallets. Failure to create either will result in a registration failure to ensure account consistency.

## Proposed Changes

### [Admin & Reset Utility]

<hr>

#### [NEW] [reset_env.py](file:///home/timh/Projects/ordex-wallet/ordex-web-wallet/scripts/reset_env.py)
- Create a standalone Python script to:
    - Purge all PostgreSQL tables.
    - Re-initialize the database schema and seed the `walletadmin` user with `changeme26`.
    - Recursively delete all wallet directories in `/data/ordexcoin/wallets` and `/data/ordexgold/wallets`.
    - Provide clear console output and safety confirmation.

### [Core Logic & RPC]

<hr>

#### [MODIFY] [rpc/__init__.py](file:///home/timh/Projects/ordex-wallet/ordex-web-wallet/backend/ordex_web_wallet/rpc/__init__.py)
- Add `unlock_wallet(user_id, chain, passphrase)` method to `DaemonManager` to facilitate `walletpassphrase` RPC calls.
- Add `is_wallet_loaded(chain, wallet_name)` helper to verify wallet state before actions.

#### [MODIFY] [api/auth.py](file:///home/timh/Projects/ordex-wallet/ordex-web-wallet/backend/ordex_web_wallet/api/auth.py)
- **Registration**: Ensure `create_user_wallet` is called for both chains. If one fails, attempt to cleanup and abort.
- **Login**: 
    - Explicitly call `load_wallet` for all registered chains upon successful authentication.
    - Attempt to `unlock_wallet` using the provided login password (assuming the wallet was encrypted with it).

### [Testing]

<hr>

#### [NEW] [test_concurrency.py](file:///home/timh/Projects/ordex-wallet/ordex-web-wallet/backend/tests/test_concurrency.py)
- A pytest-based test suite that:
    - Spawns multiple threads representing different users.
    - Simulates simultaneous login, wallet loading, and address generation.
    - Verifies that `CLIContext` correctly isolates requests and that no user receives another user's wallet info.

## Open Questions
1. Do you want the `reset_env.py` script to require a `--force` flag for execution?
2. Should we store the wallet encryption status in the database to know whether an `unlock` command is actually required at login?

## Verification Plan

### Automated Tests
- Run `pytest backend/tests/test_concurrency.py`.
- Run existing auth and wallet tests.

### Manual Verification
- Run `python3 scripts/reset_env.py` and verify the DB is clean and `walletadmin` can log in with `changeme26`.
- Register a new user and confirm both OXC and OXG wallets appear in the "Addresses" tab.
- Log in with two different browsers simultaneously and verify independent wallet operations.
