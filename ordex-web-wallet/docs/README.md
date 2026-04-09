# Ordex Web Wallet

Multi-user hosted web wallet for OrdexCoin (OXC) and OrdexGold (OXG).

## Features

- **Multi-User Support**: Multiple users can register and manage their own wallets
- **Wallet Isolation**: Each user has separate wallet files per chain
- **Secure Authentication**: Session-based auth with bcrypt password hashing
- **Admin Interface**: User management, system stats, audit logs
- **Multi-Chain**: Manage both OrdexCoin and OrdexGold
- **Backup/Restore**: Encrypted backup export/import
- **Prometheus Metrics**: Built-in metrics endpoint

## Quick Start

### 1. Configure Environment

```bash
cp docker/.env.example docker/.env
# Edit docker/.env with your passwords
```

### 2. Start Services

```bash
cd ordex-web-wallet/docker
docker-compose up -d
```

### 3. Automatic Setup

On first startup, the system automatically:
- Creates PostgreSQL database `webwallet`
- Creates all required tables
- Applies migrations (idempotent)
- Runs on every restart

Check logs: `docker logs ordex-web-wallet`

### 4. Initialize Admin (Optional)

```bash
docker exec ordex-web-wallet python -m scripts.init_admin \
    --username admin --password YourSecurePassword123
```

### 5. Access

- Web UI: http://localhost:15000
- API: http://localhost:15000/api/*
- Admin: Login with admin account → click "Admin" link

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture.

## Requirements

- Docker & Docker Compose
- PostgreSQL 15
- Python 3.11+
- ordexcoind & ordexgoldd binaries (or Docker images)

## Environment Variables

| Variable | Description |
|----------|-------------|
| DB_PASSWORD | PostgreSQL password |
| RPC_PASSWORD | RPC authentication |
| SECRET_KEY | Flask secret key (auto-generated if empty) |

## Default Ports

| Service | Port |
|---------|------|
| Web UI | 15000 |
| PostgreSQL | 5432 |
| ordexcoind RPC | 5332 |
| ordexgoldd RPC | 5333 |

## API Endpoints

### Authentication
```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

### Wallet
```
GET  /api/wallet/balance
GET  /api/wallet/addresses
POST /api/wallet/send
GET  /api/wallet/history
```

### Admin
```
GET  /api/admin/users
POST /api/admin/users/{id}/disable
POST /api/admin/users/{id}/enable
GET  /api/admin/stats
```

### System
```
GET /api/system/health
GET /api/system/metrics
```

## Security Notes

- Sessions expire after 24 hours
- Passwords hashed with bcrypt
- Rate limiting applied
- Admin actions are audit logged
- Wallet files encrypted with user passphrase

## License

MIT