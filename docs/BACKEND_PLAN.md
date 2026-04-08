# OrdexWallet Backend API Plan

## Overview
Flask-based REST API serving as the backend for OrdexWallet, communicating with ordexcoind/ordexgoldd daemons via RPC.

## API Structure

### Authentication & Wallet Management
- `POST /api/wallet/create` - Create new wallet (returns wallet info, requires backup)
- `POST /api/wallet/import` - Import existing wallet via private key
- `GET /api/wallet/info` - Get wallet information (addresses, balances)
- `POST /wallet/backup` - Backup wallet (returns encrypted backup)
- `POST /wallet/restore` - Restore wallet from backup
- `POST /wallet/verify-message` - Verify signed message
- `POST /wallet/sign-message` - Sign message with wallet

### Asset & Transaction Management
- `GET /api/assets` - Get list of assets with balances
- `GET /api/assets/{asset}` - Get specific asset details
- `GET /api/transactions` - List transactions (with filtering/pagination)
- `GET /api/transactions/{txid}` - Get transaction details
- `POST /api/transactions/send` - Create and send new transaction
- `GET /api/addresses/receive` - Get/receive addresses
- `GET /api/addresses/send` - Get/send addresses

### Market Data
- `GET /api/market/prices` - Get current prices from configured exchanges
- `GET /api/market/history/{asset}` - Get price history for asset
- `GET /api/news` - Get news from ordexnetwork homepage

### System Functionality
- `GET /api/system/stats` - Get system stats (disk, network usage)
- `GET /api/system/logs` - Get audit log entries
- `POST /api/system/rpc-console` - Execute RPC command (for debugging)
- `GET /api/system/health` - Health check endpoint

### Configuration
- `GET /api/config` - Get non-sensitive configuration
- `POST /api/config` - Update configuration (admin only)

## Core Components

### 1. RPC Client Service
Handles communication with ordexcoind/ordexgoldd daemons:
- Connection pooling
- Automatic retry with exponential backoff
- Credential management (using auto-generated random passwords)
- Method wrappers for common RPC calls

### 2. Wallet Manager
- Wallet creation/import using cryptographic libraries
- Secure private key storage (encrypted)
- Address generation (both networks)
- Transaction creation and signing
- Balance calculation

### 3. Backup System
- Automated encrypted backups on schedule
- Manual backup/restore via API
- Backup verification
- Secure storage location configuration

### 4. Input Validation
- Validation schemas for all API inputs
- Sanitization to prevent injection attacks
- Type checking and range validation
- Error responses with detailed messages

### 5. Background Tasks
- Automated backup scheduler
- Price data fetcher from exchanges
- News fetcher from ordexnetwork homepage
- System metrics collector
- Log rotation and cleanup

### 6. Security Features
- Environment-based configuration
- CORS restrictions
- Rate limiting on sensitive endpoints
- Request/response logging
- Secure headers