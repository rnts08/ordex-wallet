# OrdexWallet

A custodial web wallet for OrdexNetwork built to run with Docker in your own network.

## Overview

OrdexWallet provides a complete wallet solution for OrdexCoin (OXC) and OrdexGold (OXG):

- **Dashboard**: Asset overview, balance display, recent transactions, quick links
- **Wallet Management**: Create or import wallets, backup/restore, sign/verify messages
- **Transactions**: Send/receive, transaction history, address management
- **System**: Daemon config, system stats, RPC console, audit logs

## Architecture

```
[Docker]
    |
[Flask Backend/API] <---> [HTML/CSS/JS Frontend]
    |
    [RPC]
[ordexcoind / ordexgoldd daemons]
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Ordex network daemons (ordexcoind, ordexgoldd)

### Running with Docker

```bash
cd docker
docker-compose up -d
```

The application will be available at `http://localhost:5000`

### Development Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Configuration

On first startup, the application automatically generates:
- RPC credentials for both daemons (32-char secure passwords)
- Daemon configuration files (ordexcoind.conf, ordexgoldd.conf)
- Application configuration (config.json)

Default RPC ports:
- ordexcoind: 25173
- ordexgoldd: 25466

## API Endpoints

### Wallet
- `POST /api/wallet/create` - Create new wallet
- `POST /api/wallet/import` - Import existing wallet
- `GET /api/wallet/info` - Get wallet info
- `POST /api/wallet/backup` - Create backup
- `POST /api/wallet/restore` - Restore from backup
- `POST /api/wallet/sign-message` - Sign message
- `POST /api/wallet/verify-message` - Verify signature

### Assets
- `GET /api/assets` - Get all assets with balances
- `GET /api/assets/{asset}` - Get specific asset details

### Transactions
- `GET /api/transactions` - List transactions
- `GET /api/transactions/{txid}` - Get transaction details
- `POST /api/transactions/send` - Send transaction
- `GET /api/transactions/receive` - Get receive addresses
- `POST /api/transactions/receive/generate` - Generate new address

### System
- `GET /api/system/health` - Health check
- `GET /api/system/stats` - System statistics
- `GET /api/system/logs` - Audit logs
- `GET /api/system/config` - Daemon configuration
- `POST /api/system/config` - Update daemon config
- `POST /api/system/rpc-console` - Execute RPC command

### Market
- `GET /api/market/prices` - Get prices (fallback mode)
- `GET /api/market/news` - Get news (fallback mode)

## Testing

```bash
cd backend
source venv/bin/activate
python -m pytest tests/unit/ -v
```

## License

See [LICENSE.md](LICENSE.md) for details.

Copyright (c) 2026 ORDEX PROTOCOL. All rights reserved.