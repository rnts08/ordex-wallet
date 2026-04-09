# Multi-User Web Wallet - Implementation Plan

## Overview

Convert OrdexWallet from single-user to multi-tenant hosted wallet where each user has:
- Isolated wallet (dedicated wallet.dat per daemon)
- Personal settings and preferences
- Authentication with passphrase protection
- Separate transaction history
- Individual backup/restore

## Current Architecture Analysis

### Single-User Current State
```
┌─────────────────────────────────────────┐
│           Flask Application             │
│  ┌─────────────────────────────────┐   │
│  │      SQLite Database            │   │
│  │  - Single wallet addresses      │   │
│  │  - Single config               │   │
│  │  - Single settings             │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │   ordexcoind (1 wallet)        │   │
│  │   ordexgoldd (1 wallet)        │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Target Multi-User Architecture
```
┌─────────────────────────────────────────────────────────┐
│              Flask Application                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │    User Database (SQLite)                        │  │
│  │  - Users table (id, username, password_hash)      │  │
│  │  - Wallets table (user_id, wallet_name, chain)   │  │
│  │  - Settings table (user_id, key, value)          │  │
│  │  - Sessions table (user_id, token, expiry)       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │  ordexcoind                                    │    │
│  │    ├── wallet_user1                            │    │
│  │    ├── wallet_user2                            │    │
│  │    └── wallet_user3                            │    │
│  └───────────────────────────────────────────────┘    │
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │  ordexgoldd                                   │    │
│  │    ├── wallet_user1                            │    │
│  │    ├── wallet_user2                            │    │
│  │    └── wallet_user3                            │    │
│  └───────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Implementation Tasks

### Phase 1: User Authentication System

#### 1.1 Database Schema Changes
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE
);

-- User wallets (mapping users to daemon wallets)
CREATE TABLE wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chain TEXT NOT NULL,  -- 'ordexcoin' or 'ordexgold'
    wallet_name TEXT NOT NULL,  -- e.g., 'wallet_user1'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User settings
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sessions
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Priority**: HIGH - Foundation for all other features

#### 1.2 Authentication API
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Login, returns session token
- `POST /api/auth/logout` - Invalidate session
- `GET /api/auth/me` - Get current user info

**Priority**: HIGH

#### 1.3 Password Security
- Use bcrypt or argon2 for password hashing
- Implement minimum password requirements
- Add rate limiting on login attempts
- Support optional passphrase for wallet extra encryption

**Priority**: HIGH

### Phase 2: Wallet Isolation

#### 2.1 Per-User Wallet Creation
Currently: One wallet per daemon (`wallet`)
Target: One wallet per user per chain (`wallet_{user_id}`)

```python
# New wallet creation flow
def create_user_wallet(user_id: int, chain: str):
    wallet_name = f"wallet_{user_id}"
    if chain == "ordexcoin":
        rpc = ordexcoind_rpc
    else:
        rpc = ordexgoldd_rpc
    
    # Create wallet with encryption option
    rpc.createwallet(wallet_name, blank=True, encrypt=True)
    
    # Store wallet reference in database
    db.wallets.create(user_id=user_id, chain=chain, wallet_name=wallet_name)
```

**Priority**: HIGH

#### 2.2 RPC Client Isolation
```python
class UserRPCClient:
    def __init__(self, user_id: int, chain: str):
        user_wallet = db.wallets.get(user_id=user_id, chain=chain)
        self.wallet_name = user_wallet.wallet_name
        self.rpc = get_rpc_client(chain)
    
    def call(self, method, *args):
        # Inject wallet name for each call
        if method in WALLET_METHODS:
            args = (self.wallet_name,) + args
        return self.rpc.call(method, *args)
```

**Priority**: HIGH

#### 2.3 Wallet Loading on Login
```python
def login_user(username: str, password: str):
    user = db.users.authenticate(username, password)
    
    # Pre-load wallets for this user
    for wallet in db.wallets.get_by_user(user.id):
        rpc = get_rpc_client(wallet.chain)
        rpc.loadwallet(wallet.wallet_name)
    
    return create_session(user)
```

**Priority**: HIGH

### Phase 3: User Data Management

#### 3.1 Per-User Transaction History
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    txid TEXT NOT NULL,
    chain TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,  -- 'send' or 'receive'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Priority**: MEDIUM - Enable faster queries than RPC

#### 3.2 User Settings Storage
```python
# User preferences
user_settings = {
    "currency": "USD",
    "theme": "dark",
    "default_fee": "0.0001",
    "notifications": True,
    "send_fee": "0.0001",           # Custom send fee (user pays)
    "receive_fee": "0",             # Optional receive fee
}

# API
GET /api/user/settings
POST /api/user/settings
```

**Priority**: MEDIUM

#### 3.3 Fee Configuration
```sql
CREATE TABLE fee_config (
    id INTEGER PRIMARY KEY,
    chain TEXT NOT NULL,           -- 'ordexcoin' or 'ordexgold'
    send_fee_per_kb REAL DEFAULT 0, -- Fee per KB for sending
    receive_fee_percent REAL DEFAULT 0,  -- % fee on receive
    min_fee REAL DEFAULT 0,        -- Minimum fee
    max_fee REAL DEFAULT 0,         -- Maximum fee
    updated_at TIMESTAMP,
    updated_by INTEGER              -- Admin user ID
);

-- Per-user fee overrides
CREATE TABLE user_fee_config (
    user_id INTEGER PRIMARY KEY,
    send_fee_per_kb REAL,
    receive_fee_percent REAL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Priority**: MEDIUM - No fees from start but configurable

#### 3.4 Address Book Isolation
```sql
CREATE TABLE address_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    label TEXT,
    address TEXT NOT NULL,
    chain TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Priority**: MEDIUM

### Phase 4: Security & Isolation

#### 4.1 Session Management
- JWT or secure cookie-based sessions
- Session expiry (24h default)
- Refresh token rotation
- Concurrent session limits

**Priority**: HIGH

#### 4.2 Rate Limiting Per User
```python
# Apply rate limits per user, not global
@app limiter.limit("100 per minute", key_func=lambda: current_user.id)
def send_transaction():
    ...
```

**Priority**: HIGH

#### 4.3 Input Validation & Sanitization
- Validate all user inputs
- Prevent SQL injection
- XSS protection
- CSRF tokens for state-changing operations

**Priority**: HIGH

#### 4.4 Admin Interface (REQUIRED)
Admin interface is required for hosted wallet model:

```python
# Admin endpoints
GET    /api/admin/users           - List all users with pagination
GET    /api/admin/users/{id}       - Get user details
POST   /api/admin/users/{id}/disable - Disable user account
POST   /api/admin/users/{id}/enable - Re-enable user
DELETE /api/admin/users/{id}      - Delete user (with data wipe)
GET    /api/admin/stats            - System-wide statistics:
                                     - Total users
                                     - Active users
                                     - Total transactions
                                     - Total balance across all users
                                     - Resource usage

POST   /api/admin/fees             - Configure global fees
GET    /api/admin/fees             - Get current fee config
GET    /api/admin/logs             - Audit logs (user actions)
GET    /api/admin/health           - System health status

# Admin user creation (first admin via CLI or config)
POST /api/admin/init              - Initialize admin user
```

**Priority**: HIGH - Required for hosted model

### Phase 5: Backup & Restore

#### 5.1 Mandatory Encrypted Backup on Registration
During user registration, require encrypted backup creation:

```python
def register_user(username: str, password: str):
    # 1. Create user account
    user = db.users.create(username=username, password_hash=hash(password))
    
    # 2. Create wallets for user on both chains
    for chain in ['ordexcoin', 'ordexgold']:
        wallet_name = f"wallet_{user.id}"
        rpc = get_rpc_client(chain)
        rpc.createwallet(wallet_name, blank=True, encrypt=True, passphrase=password)
        
        # Store wallet reference
        db.wallets.create(user_id=user.id, chain=chain, wallet_name=wallet_name)
    
    # 3. Force backup creation (mandatory)
    backup = create_encrypted_backup(user.id, password)
    
    # 4. Display mnemonic/seed to user (must save)
    mnemonic = generate_mnemonic()  # Or derive from wallet seed
    db.user_settings.set(user.id, "mnemonic", mnemonic)
    
    return user, backup, mnemonic
```

**Priority**: CRITICAL - Security foundation

#### 5.2 User-Specific Backup
```python
# Per-user backup (encrypted)
def create_user_backup(user_id: int):
    # Export wallet dat files (encrypted)
    for chain in ['ordexcoin', 'ordexgold']:
        wallet_name = f"wallet_{user_id}"
        rpc = get_rpc_client(chain)
        rpc.backupwallet(f"/backups/{user_id}/{chain}.dat")
    
    # Export address book and settings
    user_data = {
        "wallets": db.wallets.get_by_user(user_id),
        "settings": db.user_settings.get_by_user(user_id),
        "address_book": db.address_book.get_by_user(user_id),
    }
    
    return backup_file
```

#### 5.3 Backup/Restore with Mnemonic
```python
# Restore via mnemonic (no password reset possible otherwise)
def restore_from_mnemonic(mnemonic: str, username: str, password: str):
    # 1. Create new account
    user = db.users.create(username=username, password_hash=hash(password))
    
    # 2. Derive wallet from mnemonic or import existing backup
    # 3. Recreate wallets with same addresses
    # 4. Set up new encryption
    
def restore_from_backup(backup_file: str, username: str, password: str):
    # 1. Decrypt backup with provided password
    # 2. Import wallet.dat to daemon
    # 3. Create user account linking to imported wallets
```

**Priority**: HIGH

### Phase 5b: Registration Flow (ENHANCED)

```python
# Enhanced registration requiring backup
POST /api/auth/register
{
    "username": "user@example.com",
    "password": "strong_password",
    "passphrase": "wallet_encryption_passphrase"
}

# Response includes critical backup info
{
    "user_id": 1,
    "mnemonic": "word1 word2 word3 ...",  # MUST SAVE THIS
    "backup_required": true,
    "message": "Save your mnemonic phrase - required for account recovery"
}
```

#### 5.2 User Restore
- Allow import of backup to different account
- Verify backup integrity before restore

**Priority**: HIGH

### Phase 6: Performance & Scaling

#### 6.1 Connection Pooling
- Reuse RPC connections where possible
- Implement connection timeout handling

#### 6.2 Async Processing
- Background job queue for:
  - Transaction broadcasting
  - Balance updates
  - Backup creation
  - Notification delivery

#### 6.3 Caching
- Cache balance queries (short TTL)
- Cache exchange rates
- Cache transaction history

### Phase 7: UI/UX Updates

#### 7.1 Login/Register Pages
- Modern authentication UI
- Password strength indicator
- Two-factor auth option (future)

#### 7.2 User Dashboard
- Per-user overview
- Switch between own wallets

#### 7.3 Admin Dashboard
- User management
- System health
- Usage statistics

## Technical Decisions Needed

### 1. Wallet Encryption Strategy

**DECISION**: Use passphrase/mnemonic-based encryption with optional encryptwallet()

The system will support both:
- **Option A**: encryptwallet() with user passphrase - True encryption, passphrase required to spend
- **Option B**: Wallet file permission only - Simpler, easy backup/restore

**Password Reset Flow**:
- Password reset requires passphrase or mnemonic phrase backup
- Users MUST create encrypted backup during registration
- Recovery only possible via mnemonic/backup import
- No "forgot password" - only backup restore possible

**Priority**: HIGH - Core security feature

### 2. Database Separation
- **Option A**: Single database with user_id foreign keys
  - Pros: Simple queries, atomic transactions
  - Cons: Permission management complex
- **Option B**: Separate database per user
  - Pros: Complete isolation, easy deletion
  - Cons: Complex query across users
- **Recommendation**: Option A for MVP

### 3. RPC Architecture
- **Option A**: Single daemon, multiple wallets
  - Pros: Single daemon process, shared resources
  - Cons: Wallet isolation depends on daemon
- **Option B**: User daemon per user (not recommended)
  - Pros: Complete isolation
  - Cons: Resource explosion
- **Recommendation**: Option A - daemon wallets are sufficient

## API Changes Summary

### Authentication Endpoints (NEW)
```
POST   /api/auth/register     - Create account
POST   /api/auth/login       - Login
POST   /api/auth/logout      - Logout
GET    /api/auth/me          - Current user
```

### User Endpoints (NEW)
```
GET    /api/user/settings    - Get user settings
POST   /api/user/settings    - Update settings
GET    /api/user/address-book - Get addresses
POST   /api/user/address-book - Save address
```

### Modified Existing Endpoints
All existing endpoints now require authentication via header:
```
Authorization: Bearer <session_token>
```

## Migration Strategy

### Phase 0: Backup
- Export current wallet data
- Document current configuration

### Phase 1: Schema Migration
- Add users table
- Migrate existing data to user_id = 1

### Phase 2: Code Changes
- Update authentication
- Update RPC calls to use user-specific wallets

### Phase 3: Testing
- Test user creation
- Test wallet isolation
- Test backup/restore

### Phase 4: Deploy
- Deploy to production
- Monitor for issues

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Wallet isolation failure | HIGH | Test thoroughly, audit RPC calls |
| User data leakage | CRITICAL | Encryption at rest, HTTPS only |
| DoS via RPC | HIGH | Rate limiting per user |
| Wallet corruption | HIGH | Regular backups, transaction logging |
| Performance degradation | MEDIUM | Monitor metrics, optimize queries |

## Timeline Estimate

| Phase | Effort | Duration |
|-------|--------|----------|
| Phase 1: Auth System | 2-3 weeks | 2 weeks |
| Phase 2: Wallet Isolation | 2-3 weeks | 2 weeks |
| Phase 3: User Data | 1-2 weeks | 1 week |
| Phase 4: Security | 2 weeks | 1 week |
| Phase 5: Backup/Restore | 1-2 weeks | 1 week |
| Phase 6-7: Performance/UI | 2-3 weeks | 2 weeks |
| **Total** | **~10-15 weeks** | **~9 weeks** |

## Open Questions (RESOLVED)

1. **Password reset flow?** 
   - RESOLVED: Password reset requires passphrase or mnemonic phrase backup. Users MUST create encrypted backup during registration. Recovery only via mnemonic/backup import. No "forgot password" - only backup restore possible.

2. **Fee management?**
   - RESOLVED: No fees collected from start, but should be configurable per-user for:
     - Send transaction fees (user pays from their balance)
     - Receive transaction fees (optional, configurable)

3. **Withdrawal limits?**
   - RESOLVED: Not required for MVP - can be added as future feature

4. **KYC requirements?**
   - RESOLVED: No KYC required - anonymous registration allowed

5. **Multi-signature support?**
   - RESOLVED: Future feature - not in MVP scope

6. **Hosted vs self-custody?**
   - RESOLVED: Hosted model - application manages wallets on behalf of users. Admin interface required for management.

7. **Admin interface needed?**
   - RESOLVED: YES - Required for hosted model:
     - User management (create, disable, delete)
     - System health monitoring
     - Fee configuration
     - Global settings management
     - Audit logs

## Related Files to Modify

- `backend/database/__init__.py` - Schema changes
- `backend/api/` - New auth endpoints, modify existing
- `backend/rpc/__init__.py` - User-specific RPC clients
- `backend/services/` - User-specific services
- `frontend/` - Login/register UI, user dashboard
- `docker/` - Possibly increase resources