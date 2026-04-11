# Ordex Web Wallet

Multi-user hosted web wallet for OrdexCoin (OXC) and OrdexGold (OXG).

## Features (Completed)

### Authentication & Security
- **Multi-User Support**: Multiple users can register and manage their own wallets
- **Wallet Isolation**: Each user has separate wallet files per chain using `-rpcwallet` flag
- **Secure Authentication**: Session-based auth with bcrypt password hashing
- **2FA/MFA Support**: TOTP-based two-factor authentication (Google Authenticator compatible)
- **Optional Email**: Email field optional during registration
- **Password Change**: Users can change their own passwords
- **Password Reset**: Admin can reset user passwords with forced change on next login
- **Audit Logging**: All admin actions are logged with timestamp, user, and details

### Admin Interface
- **User Management**: Enable/disable/delete users
- **Wallet Sweep**: Admin can sweep user funds to admin wallet
- **System Stats**: Total users, active sessions, wallets, balances, DB size
- **User List**: Searchable, sortable, paginated (25 per page)
- **Extended User Info**: Shows address count, total balance, last backup, 2FA status
- **User Details Modal**: Click username to view detailed user info, recent activity, and wallets
- **Audit Log Tab**: View all admin actions
- **Fee Configuration Tab**: Configure separate send/receive fees per chain with admin spillover addresses
- **Stake/APR Tab**: Configure staking parameters

### Wallet Features
- **Multi-Chain**: Manage both OrdexCoin (OXC) and OrdexGold (OXG)
- **Quick Send**: Modal for fast transactions from dashboard
- **Send Interface**: Network selection, balance display, Use Max button, fee calculation
- **Receive Interface**: Generate new addresses, QR codes, copy buttons
- **Import/Export WIF**: Import private keys, export (with user confirmation)
- **Maintenance Tab**: Address book (add, view, archive), wallet backup, and encryption management (set/change passphrase)

### Fee Structure
- **Auto Fee**: Use daemon-provided fees (recommended)
- **Manual Fee**: Set custom fees per chain (OXC/OXG separately configurable)
- **Admin Wallet**: Configurable address for fee surplus/spillover per chain

### Notifications (Planned)
- **User Settings**: Opt-out of reminders and notifications
- **Admin Messages**: Send individual reminders to users
- **Broadcast**: Send messages to all users
- **Backup Reminders**: Alert users who haven't backed up in N days
- **Encryption Reminders**: Alert users with unencrypted wallets

### Email Notifications (Planned)
- **Verification**: Email verification system
- **Notifications via Email**: Send email notifications to users
- **Template System**: Configurable email templates

### Staking/Yield (Planned)
- **APR Configuration**: Configurable APR per chain
- **Interval Options**: 1d, 7d, 30d staking periods
- **Auto-Stake**: Default auto-stake percentage (25/50/75/100%)
- **Global Enable/Disable**: Control staking globally

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
- Creates default admin user (walletadmin/changeme26)

Check logs: `docker logs ordex-web-wallet`

### 4. Access

- Web UI: http://localhost:15000
- API: http://localhost:15000/api/*
- Login with `walletadmin` / `changeme26`

## API Endpoints

### Authentication
```
POST /api/auth/register - Create new account
POST /api/auth/login - Login
POST /api/auth/logout - Logout
GET  /api/auth/me - Get current user
POST /api/auth/change-password - Change password
POST /api/auth/2fa/setup - Initialize 2FA
POST /api/auth/2fa/enable - Enable 2FA
POST /api/auth/2fa/disable - Disable 2FA
```

### Wallet
```
GET  /api/wallet/balance - Get balances
GET  /api/wallet/addresses - Get addresses
GET  /api/wallet/transactions - Get transaction history
POST /api/wallet/send - Send transaction
POST /api/wallet/import-wif - Import private key
POST /api/wallet/export-wif - Export private key
POST /api/wallet/addresses/generate - Generate new address
GET  /api/wallet/address-book - Get saved addresses
```

### Admin
```
GET  /api/admin/users - List users (paginated)
GET  /api/admin/users/count - User count
GET  /api/admin/users/{id}/details - Get detailed user info (wallets, balance, activity)
GET  /api/admin/stats - System statistics
POST /api/admin/users/{id}/disable - Disable user
POST /api/admin/users/{id}/enable - Enable user
POST /api/admin/users/{id}/reset-password - Reset password
POST /api/admin/users/{id}/sweep - Sweep user wallet
DELETE /api/admin/users/{id} - Delete user
GET  /api/admin/fees - Get fee config
POST /api/admin/fees - Set fee config
GET  /api/admin/stake - Get stake config
POST /api/admin/stake - Set stake config
POST  /api/admin/messages - Send message to user
POST /api/admin/messages/broadcast - Broadcast to all users
GET  /api/admin/audit - Get audit log
```

### System
```
GET /api/system/health - Health check
```

## Default Admin Account

- **Username**: walletadmin
- **Password**: changeme26
- **Initial Setup**: Must change password on first login (production)

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

## Security Notes

- Sessions expire after configured duration
- Passwords hashed with bcrypt
- All admin actions are audit logged
- Wallet files encrypted with user passphrase
- 2FA available via TOTP

## Planned Features

### Notifications System
- User opt-out settings for reminders and notifications
- In-app message center
- Email notifications (with verification)
- Backup reminders for users who haven't backed up
- Encryption reminders for users with unencrypted wallets

### Fee Management
- Per-chain fee configuration
- Auto-fee from daemon (default, recommended)
- Manual fee override
- Fee spillover to admin address

### Staking System
- Configurable APR per chain
- Multiple interval options (1d, 7d, 30d)
- Global enable/disable
- Default auto-stake percentage
- Yield accrual tracking

## License

MIT