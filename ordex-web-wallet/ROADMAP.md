# Ordex Web Wallet - Roadmap & Release Plan

## Project Status: Pre-Release (v1.0.0)

---

## Executive Summary

The Ordex Web Wallet is a **custodial web-based wallet** for OrdexCoin (OXC) and OrdexGold (OXG). It provides:
- User registration/login with bcrypt password hashing
- Dual-wallet management per user (OXC + OXG)
- Send/receive transactions
- Admin dashboard for user management
- 2FA support (TOTP)

**Architecture**: Flask backend + HTML/JS/CSS frontend + PostgreSQL + OrdexCoin/OrdexGold daemons

---

## Known Issues Fixed (v1.0.1)

### Critical Bugs Fixed
1. **Duplicate function definitions** in `frontend/js/app.js` (lines 97-117) - removed duplicates
2. **Undefined variable** in registration - `confirmPassword` was never defined
3. **Invalid RPC method** in `api/__init__.py` - `get_context()` doesn't exist, replaced with `get_blockchain_info()`
4. **Missing transaction logging** - send endpoint now logs to DB
5. **Unused imports** in backend - removed duplicate logger imports
6. **f-string validation** - fixed regex pattern syntax in validation.py

### Security Improvements
1. Transaction logging ensures audit trail
2. Input sanitization preserved
3. Session management improved

---

## Remaining Items for Production Release

### P0 - Must Fix Before Release

| # | Component | Issue | Priority |
|---|-----------|-------|----------|
| 1 | Docker | Missing `.env` file template | P0 |
| 2 | Docker | Volumes need naming for persistence | P0 |
| 3 | Config | No env validation on startup | P0 |
| 4 | Logging | Log file path `/var/log/` may not exist | P0 |

### P1 - Should Fix Before Release

| # | Component | Issue | Priority |
|---|-----------|-------|----------|
| 5 | Auth | 2FA QR code generation not displayed | P1 |
| 6 | Backup | `/backup/create` endpoint missing | P1 |
| 7 | Rate Limiting | No Redis-based rate limiting | P1 |
| 8 | Session | No refresh token mechanism | P1 |

### P2 - Good to Have

| # | Component | Issue | Priority |
|---|-----------|-------|----------|
| 9 | Fee Config | Fee estimation API incomplete | P2 |
| 10 | Fiat | No price feed integration | P2 |
| 11 | Staking | Staking UI/interaction incomplete | P2 |
| 12 | Email | No email notification system | P2 |

---

## Unit Test Coverage

### Current Tests
```
backend/tests/
├── unit/
│   ├── test_api.py           # API endpoint tests
│   ├── test_database.py      # DB operations tests
│   ├── test_validation.py  # [NEW] Address/amount validation
│   └── test_rpc.py        # [NEW] RPC DaemonManager tests
└── e2e/
    ├── test_auth_workflow.py       # Complete auth flow
    ├── test_send_workflow.py     # Send transaction
    ├── test_admin_workflow.py     # Admin operations
    └── test_wallet_retry.py     # Wallet auto-load
```

### Coverage Status
- Database operations: ~70%
- API endpoints: ~50%
- Validation: ~90%
- RPC layer: ~60%
- E2E workflows: ~40%

---

## Deployment Checklist

### Pre-Deploy
- [ ] Copy `.env.example` to `.env` and configure
- [ ] Set `SECRET_KEY` to random 32+ byte value
- [ ] Set `RPC_PASSWORD` for daemons
- [ ] Set strong `DB_PASSWORD`
- [ ] Verify Docker networks configured

### Build & Test
- [ ] Run unit tests: `pytest backend/tests/unit/ -v`
- [ ] Run E2E tests: `pytest backend/tests/e2e/ -v`
- [ ] Run linting if configured

### Deployment
- [ ] Build Docker: `docker-compose build`
- [ ] Start services: `docker-compose up -d`
- [ ] Health check: `curl http://localhost:15000/api/system/health`
- [ ] Test registration flow
- [ ] Test OXC send transaction
- [ ] Test OXG send transaction
- [ ] Test admin login

### Post-Deploy
- [ ] Change default admin password
- [ ] Set up monitoring/logging
- [ ] Configure backups
- [ ] Document incident response

---

## API Endpoints

### Authentication (`/api/auth`)
| Method | Endpoint | Auth | Description |
|--------|---------|------|------------|
| POST | `/register` | None | Register new user |
| POST | `/login` | None | Login |
| POST | `/logout` | User | Logout |
| GET | `/me` | User | Get current user |
| POST | `/change-password` | User | Change password |
| POST | `/2fa/setup` | User | Generate 2FA secret |
| POST | `/2fa/enable` | User | Enable 2FA |
| POST | `/2fa/disable` | User | Disable 2FA |
| POST | `/delete` | User | Delete account |

### Wallet (`/api/wallet`)
| Method | Endpoint | Auth | Description |
|--------|---------|------|------------|
| GET | `/balance` | User | Get balances |
| GET | `/addresses` | User | Get addresses |
| POST | `/send` | User | Send transaction |
| GET | `/transactions` | User | Get transactions |
| POST | `/addresses/generate` | User | Generate address |
| POST | `/import-wif` | User | Import WIF key |
| POST | `/export-wif` | User | Export WIF key |
| POST | `/backup` | User | Backup wallet |
| POST | `/encrypt` | User | Encrypt wallet |

### Admin (`/api/admin`)
| Method | Endpoint | Auth | Description |
|--------|---------|------|------------|
| GET | `/users` | Admin | List users |
| GET | `/stats` | Admin | System stats |
| POST | `/messages/broadcast` | Admin | Broadcast |
| POST | `/users/<id>/sweep` | Admin | Sweep wallet |
| POST | `/maintenance/*` | Admin | Maintenance |

### System (`/api/system`)
| Method | Endpoint | Auth | Description |
|--------|---------|------|------------|
| GET | `/health` | None | Health check |
| GET | `/metrics` | None | Prometheus metrics |

---

## Security Considerations

### For Custodial Wallet
1. **Hot wallet risk** - All funds stored in daemon wallets
2. **Admin access** - Single admin can sweep any wallet
3. **2FA recommended** - Enable for all users
4. **Backup很重要** - Wallet.dat backed up as encrypted

### Recommended Security Measures
1. Enable 2FA on all accounts
2. Use hardware wallet for admin
3. Configure regular automated backups
4. Monitor for suspicious activity
5. Use separate admin machine
6. Enable daemon firewall rules

---

## Version History

| Version | Date | Changes |
|---------|------|--------|
| 1.0.0 | 2026-04-11 | Initial release |
| 1.0.1 | 2026-04-11 | Bug fixes post-analysis |

---

*Last Updated: 2026-04-11*