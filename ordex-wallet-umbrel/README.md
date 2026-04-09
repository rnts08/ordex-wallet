# OrdexWallet for Umbrel

A complete custodial web wallet for OrdexNetwork - run your own self-hosted wallet for OrdexCoin (OXC) and OrdexGold (OXG) directly on your Umbrel device.

## Features

- **Dashboard**: Real-time balance display for OXC and OXG, network sync status, recent transactions
- **Wallet Management**: Create new wallets or import existing ones with private keys
- **Transactions**: Send OXC/OXG to any address, generate receive addresses, view transaction history
- **Backup & Restore**: Encrypted wallet backups with optional passphrase protection
- **System Management**: Daemon configuration, RPC console, system statistics, audit logging
- **Message Signing**: Sign and verify messages with wallet addresses

## Installation

1. Open your Umbrel device
2. Go to the App Store
3. Search for "OrdexWallet"
4. Click Install
5. Wait for installation to complete
6. Access the wallet at `http://umbrel.local:15000`

## Platform Support

### ✅ Supported
- **x86/x64 (Intel/AMD)**: Full support with pre-compiled daemon binaries

### ⚠️ Limited Support  
- **ARM64**: Manual compilation of daemon binaries required (see PLATFORM_SUPPORT.md)

## Getting Started

1. **Create Wallet**: Navigate to the Wallet page and click "Create New Wallet"
2. **Import Wallet**: Use the "Import Wallet" feature with private keys
3. **Send Transactions**: Use the Send page to transfer OXC/OXG
4. **Backup**: Create encrypted backups of your wallet

## Configuration

The app automatically configures daemon connections and manages all blockchain data storage in persistent volumes.

### Environment Variables
- `PORT`: Web server port (15000)
- `CONFIG_DIR`: Configuration directory (/data/config)
- `DATA_DIR`: Data storage directory (/data)
- `FLASK_ENV`: Flask environment (production)

### Volume Usage
All data persists in the `APP_DATA_DIR` volume:
- `/data/config` - Daemon configuration files
- `/data/blockchain/ordexcoin` - OrdexCoin blockchain data
- `/data/blockchain/ordexgold` - OrdexGold blockchain data
- `/data/ordexwallet.db` - Application database
- `/data/backups` - Wallet backups
- `/data/logs` - Application logs

## Support

For issues and support:
- GitHub Issues: https://github.com/OrdexCoin/ordex-wallet/issues
- Documentation: See PLATFORM_SUPPORT.md for ARM64 compilation instructions

## External Links

| Service | URL |
|---------|-----|
| Block Explorer (OXC) | https://explorer.ordexcoin.com |
| Block Explorer (OXG) | https://explorer.ordexgold.com |
| Swap | https://ordexswap.online |
| Network Site | https://ordexnetwork.org |

## License

See LICENSE.md for details.