# OrdexWallet Features

## Core Features

### Dashboard
- Real-time balance display for OXC (OrdexCoin) and OXG (OrdexGold)
- Network sync status for both chains
- Recent transactions list
- Quick access to send/receive actions

### Wallet Management
- **Create New Wallet**: Generate new wallet with addresses for both OXC and OXG
- **Import Wallet**: Import existing wallet using private key (WIF format)
- **Multiple Addresses**: Support for multiple receive addresses per chain
- **Address Book**: Save frequently used addresses

### Transaction Management
- **Send**: Send OXC or OXG to any address
  - Custom fee selection
  - Transaction preview before confirmation
- **Receive**: Generate new receive addresses
- **History**: View complete transaction history with status
- **Details**: View individual transaction details (txid, confirmations, inputs/outputs)

### Backup & Restore
- **Create Backup**: Export encrypted wallet backup
- **Passphrase Protection**: Optional AES-256 encryption with user-provided passphrase
- **Restore**: Import backup file to recover wallet
- **Restore from Private Key**: Direct private key import as fallback

### System Management
- **Daemon Configuration**: View and edit daemon settings
- **RPC Console**: Execute raw RPC commands for debugging
- **System Statistics**: Memory usage, disk space, uptime
- **Audit Logging**: Track all operations with timestamps

### Message Signing
- **Sign Message**: Sign a message with a wallet address
- **Verify Message**: Verify a signature from another address

## Technical Features

### Security
- Non-root user execution in containers
- Encrypted backup files (AES-256)
- Secure credential generation
- RPC credentials stored with 0600 permissions

### Auto-Configuration
- Automatic RPC credential generation on first startup
- Daemon configuration files auto-created
- Blockchain data directory initialization

### Multi-Chain Support
- OrdexCoin (OXC) - Primary chain
- OrdexGold (OXG) - Secondary chain
- Independent daemon management per chain

### Volume Mounts
- Config persistence: `${APP_DATA_DIR}/config`
- Blockchain data: `${APP_DATA_DIR}/blockchain/{ordexcoin,ordexgold}`
- Database: `${APP_DATA_DIR}/ordexwallet.db`
- Backups: `${APP_DATA_DIR}/backups`
- Logs: `${APP_DATA_DIR}/logs`

## API Endpoints

### Wallet API
- `POST /api/wallet/create` - Create new wallet
- `POST /api/wallet/import` - Import existing wallet
- `GET /api/wallet/info` - Get wallet information
- `POST /api/wallet/backup` - Create wallet backup
- `POST /api/wallet/restore` - Restore from backup
- `POST /api/wallet/sign-message` - Sign a message
- `POST /api/wallet/verify-message` - Verify signature

### Assets API
- `GET /api/assets` - Get all assets with balances
- `GET /api/assets/ordexcoin` - Get OXC details
- `GET /api/assets/ordexgold` - Get OXG details

### Transactions API
- `GET /api/transactions` - List transactions
- `GET /api/transactions/{txid}` - Get transaction details
- `POST /api/transactions/send` - Send transaction
- `GET /api/transactions/receive` - Get receive addresses
- `POST /api/transactions/receive/generate` - Generate new address

### System API
- `GET /api/system/health` - Health check
- `GET /api/system/stats` - System statistics
- `GET /api/system/logs` - Audit logs
- `GET /api/system/config` - Get daemon configuration
- `POST /api/system/config` - Update daemon configuration
- `POST /api/system/rpc-console` - Execute RPC command

## Deployment Options

### Standalone Docker
- Port: 15000 (mapped from internal 5000)
- Uses named volume for data persistence
- Suitable for local or self-hosted deployment

### Umbriel App Store
- Port: 15000 (Umbriel standard)
- Uses `${APP_DATA_DIR}` volume mounts
- Compatible with umbrelOS

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| x86/x64 | Full | Pre-compiled daemons |
| ARM64 | Limited | Requires manual compilation |

## Dependencies

### Runtime
- Python 3.12+
- Flask + CORS
- SQLite3
- ordexcoind (OrdexCoin daemon)
- ordexgoldd (OrdexGold daemon)

### System
- Docker Engine 20.10+
- Docker Compose v2+
- 2GB+ RAM
- 10GB+ storage