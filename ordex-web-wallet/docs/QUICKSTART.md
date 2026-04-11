# Ordex Web Wallet

Multi-user hosted web wallet for OrdexCoin (OXC) and OrdexGold (OXG).

## Overview

Ordex Web Wallet is a hosted multi-user wallet solution built from the OrdexWallet self-hosted code. It provides:

- User registration and authentication
- Per-user wallet isolation
- Admin management interface
- Backup/restore functionality

## Quick Start

```bash
# 1. Configure
cp docker/.env.example docker/.env
# Edit docker/.env

# 2. Start
cd docker
docker-compose up -d

# 3. Automatic - database tables created on startup
# Check logs: docker logs ordex-web-wallet | grep "Database"

# 4. (Optional) Initialize admin
docker exec ordex-web-wallet python -m scripts.init_admin \
    --username admin --password "YourPassword123"

# 5. Access: http://localhost:15000
```

## Auto-Initialization

The system automatically:
- Creates PostgreSQL database (if not exists)
- Creates all tables on first start
- Runs migrations on every startup (idempotent)
- Survives database restarts

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design
- [Operations](docs/OPERATIONS.md) - Deployment & maintenance
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

## Requirements

- Docker & Docker Compose
- PostgreSQL 15+
- Python 3.11+

## Features

| Feature | Description |
|---------|-------------|
| Multi-user | Multiple user accounts |
| Wallet isolation | Per-user wallet files |
| Authentication | Session-based login |
| Admin interface | User management |
| Backup | Encrypted exports |
| Metrics | Prometheus endpoint |

## License

MIT