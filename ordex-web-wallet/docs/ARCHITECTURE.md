# Ordex Web Wallet - Architecture

## Overview

Multi-user hosted web wallet built from OrdexWallet self-hosted code. Provides user authentication, isolated wallets per user, and admin management interface.

## System Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                    ordex-web-wallet/                                                  │
│                                                                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ ┌──────────────────────┐  │
│  │   webwallet  │ │  postgres    │ │    ordexcoind        │ │    ordexgoldd        │  │
│  │  (Flask)     │ │  (Database)  │ │    (OXC daemon)      │ │    (OXG daemon)      │  │
│  │   :5000      │ │   :5432      │ │    :5332             │ │    :5333             │  │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ └──────────────────────┘  │
│         │                 │                 │                     │                   |
│         └─────────────────┴─────────────────┼─────────────────────┘                   |
│                                             │                                         |
└───────────────────────────────────────────────────────────────────────────────────────┘
             │                │                │
        ┌────┴────────────────┴────────────────┴────┐
        │         Shared Volume: ordexweb_data      │
        │  ┌──────────────────────────────────────┐ │  
        │  │ /data/blocks/     - Blockchain data  │ │
        │  │ /data/chainstate/ - Chain state      │ │
        │  │ /data/wallets/    - wallet_*.dat     │ │   
        │  │ /data/backups/    - User backups     │ │
        │  │ /data/logs/       - App logs         │ │
        │  └──────────────────────────────────────┘ │
        └───────────────────────────────────────────┘
```

## Container Services

| Service | Port | Image | Purpose |
|---------|------|-------|---------|
| webwallet | 5000 | custom | Flask application |
| postgres | 5432 | postgres:15-alpine | User database |
| ordexcoind | 5332 | ordexnetwork/ordexcoind | OXC daemon |
| ordexgoldd | 5333 | ordexnetwork/ordexgoldd | OXG daemon |

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  webwallet_network (172.16.1.0/24)                          │
│  - webwallet ↔ postgres                                     │
│  - webwallet ↔ ordexcoind                                   │
│  - webwallet ↔ ordexgoldd                                   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  daemon_network (172.16.2.0/24)                             │
│  - ordexcoind internal                                      │
│  - ordexgoldd internal                                      │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
UserBrowser ──HTTP──> webwallet:5000 ──CLI──> ordexcoind:5332
                     │                  │
                     │                  └──> /data/wallets/wallet_{user_id}_ordexcoin.dat
                     │
                     └──SQL──> postgres:5432
                              │
                              └──> users, sessions, settings, audit
```

## Database Schema

### Core Tables

```sql
-- Users (hosted accounts)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

-- User wallets (mapping to daemon wallets)
CREATE TABLE user_wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chain TEXT NOT NULL CHECK (chain IN ('ordexcoin', 'ordexgold')),
    wallet_name TEXT NOT NULL,
    wallet_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User settings
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    UNIQUE(user_id, setting_key)
);

-- Address book
CREATE TABLE address_book (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label TEXT,
    address TEXT NOT NULL,
    chain TEXT NOT NULL,
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction cache
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    txid TEXT NOT NULL,
    chain TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('send', 'receive')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin audit log
CREATE TABLE admin_audit (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,
    target_user_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Wallet Isolation

### Per-User Wallets

Each user gets dedicated wallet files:

```
/data/wallets/
├── wallet_1_ordexcoin.dat     # User 1 OXC
├── wallet_1_ordexgold.dat    # User 1 OXG
├── wallet_2_ordexcoin.dat    # User 2 OXC
├── wallet_2_ordexgold.dat    # User 2 OXG
└── ...
```

### Wallet Access Method

Uses `-rpcwallet` CLI parameter for isolation:
```bash
ordexcoin-cli -rpcwallet=wallet_1_ordexcoin getbalance
ordexgold-cli -rpcwallet=wallet_2_ordexgold getnewaddress
```

## API Design

### Authentication Endpoints
```
POST /api/auth/register     - Create account
POST /api/auth/login       - Login
POST /api/auth/logout     - Logout
GET  /api/auth/me         - Current user info
```

### User Endpoints (auth required)
```
GET  /api/wallet/balance    - Get balances
GET  /api/wallet/addresses - Get addresses
POST /api/wallet/send      - Send transaction
GET  /api/wallet/history   - Transaction history
GET  /api/user/settings   - Get settings
POST /api/user/settings   - Update settings
POST /api/backup/create   - Create backup
POST /api/backup/restore - Restore backup
```

### Admin Endpoints (admin required)
```
GET  /api/admin/users          - List users
GET  /api/admin/users/{id}    - User details
POST /api/admin/users/{id}/disable
POST /api/admin/users/{id}/enable
DELETE /api/admin/users/{id}
GET  /api/admin/stats        - System stats
GET  /api/admin/fees       - Get fees
POST /api/admin/fees       - Set fees
```

### System Endpoints
```
GET /api/system/health    

### Admin Functions
The administrative panel allows system administrators to manage users, monitor system health, and configure global settings.

- **User Management**:
    - List/Search users with pagination and sorting.
    - View deep user details (wallets, recent transactions, last login).
    - Enable/Disable accounts (prevents session creation).
    - Hard delete users (destructive).
    - Reset user passwords (requires admin override).
    - Wallet Sweep: Transfer all funds from a user's wallet to a specified admin address.
- **Global Settings**:
    - Fee Configuration: Set send/receive fees per chain.
    - Stake Configuration: Set APR and lock intervals for staking rewards.
- **Communication**:
    - Individual user messages (Reminders/Alerts).
    - Global broadcast announcements.
- **Monitoring**:
    - System Statistics: Total users, active sessions, blockchain balances, storage usage.
    - Audit Logs: Full history of all administrative actions.

### Audit Logging & Security
All administrative actions MUST be recorded in the `admin_audit` table.
- **Required Fields**: `admin_user_id`, `action`, `target_user_id` (if applicable), `details` (JSON), `created_at`.
- **Sensitive Actions**: Resetting passwords, sweeping wallets, and broadcasting messages require high-visibility logging in both the database and server-side log files.
- **Confirmation**: Destructive actions (Delete, Sweep, Disable) require double-confirmation in the frontend.
```

## Security Design

### Isolation Layers

1. **Network**: Separate Docker networks
2. **Database**: Row-level user_id filtering
3. **RPC**: Wallet name isolation via `-rpcwallet` flag
4. **Authentication**: Session tokens with expiry

### Security Features

- bcrypt password hashing
- Session tokens (URL-safe random)
- 24-hour session expiry
- Rate limiting (per-user)
- Admin audit logging
- SQL injection prevention (parameterized queries)

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes | - | PostgreSQL URL |
| OXRPC_URL | Yes | http://ordexcoind:5332 | OXC RPC URL |
| OGRPC_URL | Yes | http://ordexgoldd:5333 | OXG RPC URL |
| RPC_USER | Yes | ordex | RPC username |
| RPC_PASS | Yes | - | RPC password |
| SECRET_KEY | No | auto-generated | Flask secret |
| SESSION_DURATION | No | 86400 | Session seconds |

## File Structure

```
ordex-web-wallet/
├── backend/
│   ├── app.py              # Flask app factory
│   ├── config/__init__.py  # Configuration
│   ├── database/__init__.py # DB schema & queries
│   ├── rpc/__init__.py     # CLI-based RPC
│   ├── middleware/auth.py   # Auth decorators
│   ├── api/
│   │   ├── __init__.py    # System endpoints
│   │   ├── auth.py       # Auth endpoints
│   │   ├── wallet.py    # Wallet endpoints
│   │   └── admin.py     # Admin endpoints
│   └── requirements.txt
├── frontend/
│   ├── index.html        # SPA entry
│   ├── css/style.css     # OrdexNetwork styles
│   ├── js/app.js        # Frontend JS
│   └── *.png            # Logos
├── docker/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── docker-compose.yml
│   └── .env.example
├── scripts/
│   └── init_admin.py     # Admin initialization
├── bin/                 # CLI tools & daemons
├── docs/
│   ├── ARCHITECTURE.md
│   ├── README.md
│   ├── OPERATIONS.md
│   └── TROUBLESHOOTING.md
└── README.md
```

## Scalability

- Read replicas for blockchain queries (future)
- Background workers for heavy tasks (future)
- Redis for sessions/caching (future)

## Differences from Self-Hosted

| Feature | Self-Hosted | Web Wallet |
|---------|------------|-----------|
| Users | Single | Multi-tenant |
| Database | SQLite | PostgreSQL |
| Auth | None | Session-based |
| Wallet | Single | Per-user |
| Admin | N/A | Full interface |
| Backup | Manual | Automated |
| Isolation | N/A | Complete |