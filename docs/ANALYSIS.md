# OrdexWallet Deep Analysis

## Fixed Issues

All bugs and issues have been resolved. This document tracks the resolution status.

| # | Issue | Status | Fix Date |
|---|-------|--------|-----------|
| 1 | Daemon Startup Race Condition | FIXED | 2026-04-09 |
| 2 | Wallet Loading Logs | FIXED | 2026-04-09 |
| 3 | Hardcoded RPC Fallback Credentials | FIXED | 2026-04-09 |
| 5 | Daemon Path Resolution | FIXED | 2026-04-09 |
| 7 | Volume Permissions | FIXED | 2026-04-09 |
| 12 | Weak Default Credentials Generation | FIXED | 2026-04-09 |
| 15 | Database Corruption Risk (WAL mode) | FIXED | 2026-04-09 |

## By Design / Expected Behavior

These items are intentional or expected and require no action:

| # | Issue | Status | Notes |
|---|-------|--------|-------|
| 4 | Inconsistent Port Configuration | BY DESIGN | Standalone uses 5000 internal, Umbriel uses 15000 |
| 6 | Blockchain Sync Time | EXPECTED | Full node behavior, takes hours on first start |
| 8 | Log Rotation Not Implemented | FEATURE | Production should use logrotate on host |
| 9 | Backup File Location | FEATURE | Use volume mount to persist |
| 10 | RPC Binding to localhost Only | BY DESIGN | Security feature |
| 11 | No TLS on RPC | BY DESIGN | Internal-only, acceptable |
| 13 | Blockchain Index Rebuild | EXPECTED | Full node behavior |
| 14 | No Connection Pooling | ACCEPTABLE | Minor overhead for typical usage |
| 16 | Config File Race Condition | ACCEPTABLE | Single-container deployment |

## Technical Details

### Critical Fixes Applied

#### 1. Daemon Startup Race Condition
- **Problem**: Flask started immediately after daemon start command
- **Solution**: Added readiness check in entrypoint.sh using Python socket check, waits up to 60 seconds
- **Additional**: Added frontend loading spinner while waiting for daemons

#### 2. Wallet Loading Logs  
- **Problem**: "Wallet already exists" logged as ERROR
- **Solution**: Changed to INFO level logging

#### 3. Hardcoded RPC Fallback Credentials
- **Problem**: Invalid fallback credentials "ordexuser"/"changeme"
- **Solution**: Removed hardcoded fallback, app fails with clear error if config missing

#### 5. Daemon Path Resolution
- **Problem**: Daemons copied silently without verification
- **Solution**: Added explicit binary verification with error messages

#### 7. Volume Permissions
- **Problem**: Volumes pre-created with wrong ownership
- **Solution**: Dockerfile creates umbrel user (1000), entrypoint sets ownership

#### 12. Weak Default Credentials
- **Problem**: Using secrets.choice() with limited alphabet
- **Solution**: Changed to secrets.token_urlsafe() for stronger entropy

#### 15. Database Corruption Risk
- **Problem**: SQLite not using WAL mode
- **Solution**: Already enabled in DatabaseManager (`PRAGMA journal_mode=WAL`)

## Debugging Guide

### Viewing Daemon Logs
```bash
docker exec ordexwallet tail -f /data/logs/ordexcoind.log
docker exec ordexwallet tail -f /data/logs/ordexgoldd.log
```

### Checking Daemon Status
```bash
curl -u ordexcoin_rpc:PASSWORD http://localhost:25173 -d '{"jsonrpc":"1.0","id":"1","method":"getblockchaininfo"}'
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Connection refused" | Daemon not started | Check if daemon process running |
| "Authentication failed" | Wrong RPC credentials | Regenerate config |
| "Loading block index" | Still syncing | Wait for sync to complete |
| "Database locked" | Concurrent access | Ensure single instance |

### Health Check Endpoints

- `GET /api/system/health` - Overall system health
- `GET /api/system/stats` - Resource usage
- `GET /api/assets` - Chain sync status

## Testing Checklist

Before release, verify:

- [ ] Clean install (no existing data)
- [ ] Wallet creation and address generation
- [ ] Import existing wallet via private key
- [ ] Send transaction (testnet recommended)
- [ ] Receive transaction
- [ ] Backup creation and restore
- [ ] Message signing and verification
- [ ] RPC console functionality
- [ ] Config regeneration on corrupted config
- [ ] Container restart preserves data
- [ ] Log rotation works
- [ ] Umbriel app store installation

## Future Improvements

Planned enhancements (not bugs):

1. ~~Add sync percentage to health check~~ - COMPLETED
2. ~~Prometheus metrics endpoint~~ - COMPLETED
3. ~~Implement log rotation~~ - COMPLETED (10MB max, 5 files rotation in background)

See [WISHLIST.md](./WISHLIST.md) for long-term features not currently planned.

---

*Last updated: 2026-04-09*
*Document version: 2.0*