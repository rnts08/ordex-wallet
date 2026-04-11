# AGENTS.md - Ordex Web Wallet

## Project Structure

```
ordex-web-wallet/
├── backend/           # Flask application
│   ├── api/          # API blueprints (auth, wallet, admin, system)
│   ├── database/     # PostgreSQL operations
│   ├── rpc/         # DaemonManager for OXC/OXG RPC
│   ├── middleware/ # Auth decorators
│   ├── utils/       # Validation helpers
│   └── tests/      # Unit + E2E tests
├── frontend/        # HTML/JS/CSS
├── docker/           # Docker Compose
└── bin/             # CLI binaries (ordexcoind, ordexgoldd)
```

## Key Commands

### Run Tests
```bash
cd backend && source ../.venv/bin/activate
pytest tests/unit/test_validation.py tests/unit/test_rpc.py -v
```

### Start Services
```bash
cd docker && cp .env.example .env  # Configure first
docker-compose up -d
```

### Health Check
```bash
curl http://localhost:15000/api/system/health
```

## Critical Setup Steps

1. **Copy env file**: `cp docker/.env.example docker/.env` before `docker-compose up`
2. **Set passwords**: `DB_PASSWORD`, `RPC_PASSWORD`, `SECRET_KEY` in `.env`
3. **Change admin password**: Login with `walletadmin` / `changeme26`, change immediately

## Important Quirks

- **Dual wallet creation**: Registration creates BOTH ordexcoin AND ordexgold wallets automatically
- **Transaction logging**: Send endpoint writes to `transactions` table after successful RPC call
- **Wallet naming**: Daemon uses format `wallet_{user_id}_{chain}` (e.g., `wallet_1_ordexcoin`)
- **Default admin**: `walletadmin` / `changeme26` - created on first DB init
- **Ports**: Web UI on 15000, RPC 5332 (OXC) / 5333 (OXG)

## Package Boundaries

- `backend/api/auth.py` - Registration, login, 2FA, account management
- `backend/api/wallet.py` - Balance, send, receive, addresses
- `backend/api/admin.py` - User management, stats, sweep, broadcast
- `backend/rpc/__init__.py` - DaemonManager wraps all daemon RPC calls
- `backend/database/__init__.py` - All DB operations, schema, migrations

## Common Pitfalls

- **Duplicate function names**: Check before adding to `app.js` - duplicates cause silent failures
- **Undefined variables**: Always use `document.getElementById()` for DOM values
- **Transaction logging**: Always record after successful `send_from_user()`
- **Wallet unlock**: Call `load_wallet()` before any operation on user's wallet

## References

- ROADMAP.md - Release plan with known issues
- README.md - Feature overview and API docs
- implementation_plan.md - Previous implementation details