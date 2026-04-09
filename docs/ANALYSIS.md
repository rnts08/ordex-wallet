# OrdexWallet Deep Analysis

## Known Issues & Limitations

### Critical Issues

#### 1. Daemon Startup Race Condition
**Status**: FIXED
**Description**: Flask starts immediately after daemon start command, but daemons may not be ready to accept RPC connections. The 5-second sleep may not be sufficient on slow systems or during initial blockchain download.
**Fix**: Added daemon readiness check in entrypoint.sh using Python socket check, waits up to 60 seconds for daemons to become available. Added frontend loading spinner while waiting.

#### 2. Wallet Loading Not Persisted
**Status**: FIXED
**Description**: Each container restart re-loads the wallet, which may cause address history to not load immediately.
**Fix**: Improved logging - now logs info "Wallet already exists for X, loading..." instead of ERROR. Health endpoint returns proper status during initialization.

### Logical Errors

#### 3. Hardcoded RPC Fallback Credentials
**Status**: FIXED
**Description**: If config generation fails, the app falls back to hardcoded "ordexuser"/"changeme" credentials that won't work.
**Fix**: Removed hardcoded fallback. App now fails with clear error if config cannot be loaded.

#### 4. Inconsistent Port Configuration
**Status**: INFO (by design)
**Description**: 
- Standalone Docker: internal port 5000, external 15000
- Umbriel: internal port 15000
**Note**: Both expose 15000 externally but Flask listens on different internal ports. Documented in README.

#### 5. Daemon Path Resolution
**Status**: FIXED
**Description**: Entry script copies daemons from `/data/bin` but doesn't verify the source location exists first.
**Fix**: Added explicit daemon binary verification in entrypoint.sh with clear error messages.

### Operations Issues

#### 6. Blockchain Sync Time
**Status**: INFO
**Description**: Initial blockchain download can take hours depending on network and chain size.
**Note**: Expected behavior for full node operation.
**Impact**: Wallet won't show balances until synced.
**Monitoring**: Use `getblockchaininfo` via RPC console to check sync progress.

#### 7. Volume Permissions
**Severity**: Medium
**Description**: If volumes are pre-created with wrong ownership, daemon config write fails.
**Impact**: Container exits with error.
**Fix**: Ensure volumes are owned by user 1000 (umbrel) or run with explicit uid mapping.

#### 8. Log Rotation Not Implemented
**Severity**: Low
**Description**: Application logs grow indefinitely.
**Impact**: Disk space exhaustion on long-running instances.
**Workaround**: Mount logs to host and implement external rotation.

#### 9. Backup File Location
**Severity**: Low
**Description**: Backups stored in container volume, not exported to host by default.
**Impact**: Backups lost on container deletion.
**Workaround**: Use `${APP_DATA_DIR}/backups` volume mount to persist.

## Security Considerations

### 10. RPC Binding to localhost Only
**Description**: Daemons bind RPC to 127.0.0.1 only.
**Impact**: No external RPC access (intended security).
**Note**: Correct for wallet use case.

### 11. No TLS on RPC
**Description**: RPC communication is unencrypted within container.
**Impact**: Internal-only (not exposed externally).
**Note**: Acceptable for localhost-only RPC.

### 12. Weak Default Credentials Generation
**Description**: Uses Python's `secrets.choice()` for password generation.
**Impact**: Adequate for local/development.
**Note**: Consider using `secrets.token_urlsafe()` for longer strings.

## Performance Issues

### 13. Blockchain Index Rebuild
**Description**: On first start, daemons build txindex which is resource-intensive.
**Impact**: High CPU and I/O during initial sync.
**Note**: This is expected behavior for full node operation.

### 14. No Connection Pooling
**Description**: Each RPC call creates new HTTP connection.
**Impact**: Minor overhead on high-frequency calls.
**Note**: Not noticeable for typical wallet usage.

## Data Integrity

### 15. Database Corruption Risk
**Status**: FIXED
**Description**: SQLite database not using WAL mode, may corrupt on unclean shutdown.
**Fix**: WAL mode already enabled in DatabaseManager (`PRAGMA journal_mode=WAL`).

### 16. Config File Race Condition
**Description**: Multiple containers starting simultaneously could both try to generate config.
**Impact**: Possible corrupted config files.
**Note**: Single-container deployment makes this unlikely.

## Debugging Guide

### Viewing Daemon Logs
```bash
# Inside container
docker exec -it ordexwallet bash
tail -f /data/logs/ordexcoind.log
tail -f /data/logs/ordexgoldd.log
```

### Checking Daemon Status
```bash
# Via RPC
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

1. Implement WAL mode for SQLite
2. Add health check for daemon sync percentage
3. Implement proper log rotation
4. Add Prometheus metrics endpoint
5. Support for hardware wallet integration
6. Multi-signature wallet support
7. Lightning Network integration (future OXC feature)