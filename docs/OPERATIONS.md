# OrdexWallet Operations Guide

## Daily Operations

### Starting the Wallet

```bash
cd docker
docker compose up -d
```

### Stopping the Wallet

```bash
cd docker
docker compose down
```

### Viewing Logs

```bash
# All logs
docker compose logs -f

# Specific service
docker compose logs -f ordexwallet

# Last 100 lines
docker compose logs --tail=100
```

### Accessing the Container

```bash
# Interactive shell
docker compose exec ordexwallet bash

# Run single command
docker compose exec ordexwallet python -c "import app; print('OK')"
```

## Monitoring

### Check Daemon Status

Via RPC console in UI or:
```bash
docker exec ordexwallet curl -s -u ordexcoin_rpc:$(cat /data/config/ordexcoin.conf | grep rpcpassword | cut -d= -f2) http://localhost:25173 -d '{"jsonrpc":"1.0","id":"1","method":"getblockchaininfo"}'
```

### Check Sync Status

```json
{
  "jsonrpc": "1.0",
  "id": "1",
  "method": "getblockchaininfo",
  "params": []
}
```

Key fields:
- `blocks` vs `headers` - should be equal when synced
- `initialblocksdownload` - true until initial sync complete

### Check Wallet Balance

```json
{
  "jsonrpc": "1.0", 
  "id": "1",
  "method": "getbalance",
  "params": ["*", 1]
}
```

## Troubleshooting

### Container Won't Start

1. Check logs:
   ```bash
   docker compose logs
   ```

2. Verify volume permissions:
   ```bash
   ls -la data/
   ```

3. Check port availability:
   ```bash
   lsof -i :15000
   ```

### Daemon Won't Start

1. Check daemon binaries exist:
   ```bash
   docker exec ordexwallet ls -la /usr/local/bin/ordex*
   ```

2. Check config exists:
   ```bash
   docker exec ordexwallet ls -la /data/config/
   ```

3. Check logs for errors:
   ```bash
   docker exec ordexwallet cat /data/logs/ordexcoind.log
   ```

### RPC Connection Failed

1. Verify daemon is running:
   ```bash
   docker exec ordexwallet ps aux | grep ordex
   ```

2. Check RPC port is listening:
   ```bash
   docker exec ordexwallet netstat -tlnp | grep 25173
   ```

3. Verify credentials in config:
   ```bash
   docker exec ordexwallet cat /data/config/ordexcoind.conf | grep -E "^(rpcuser|rpcpassword|rpcport)"
   ```

### Wallet Empty After Restart

This is normal during initial sync. Wait for blockchain to sync:
```bash
# Check sync progress
docker exec ordexwallet ordexcoind getblockchaininfo
```

### High Resource Usage

1. Check daemon processes:
   ```bash
   docker exec ordexwallet top
   ```

2. Limit connections:
   ```bash
   # Add to ordexcoind.conf
   maxconnections=8
   ```

3. Limit database cache:
   ```bash
   # Add to ordexcoind.conf
   dbcache=256
   ```

## Backup & Recovery

### Manual Backup

```bash
# Backup database
docker exec ordexwallet cp /data/ordexwallet.db /data/backups/wallet-$(date +%Y%m%d).db

# Backup configs
docker exec ordexwallet tar -czf /data/backups/configs-$(date +%Y%m%d).tar.gz /data/config/

# Copy to host
docker cp ordexwallet:/data/backups/ ./local-backups/
```

### Restore from Backup

```bash
# Stop wallet
cd docker
docker compose down

# Restore database
docker cp local-backups/wallet-YYYYMMDD.db ordexwallet:/data/ordexwallet.db

# Restore configs
docker cp local-backups/configs-YYYYMMDD.tar.gz ordexwallet:/data/
docker exec ordexwallet tar -xzf /data/configs-YYYYMMDD.tar.gz -C /

# Start wallet
docker compose up -d
```

### Export Private Keys

```bash
docker exec ordexwallet ordexcoind dumpwallet /data/backups/wallet.txt
docker cp ordexwallet:/data/backups/wallet.txt ./
```

## Maintenance

### Clear Blockchain Data (Not Recommended)

```bash
docker compose down
rm -rf data/blockchain/
docker compose up -d
```

Note: This forces full resync and may take hours.

### Update Daemon Binaries

```bash
# Stop
docker compose down

# Remove old binaries
rm bin/ordexcoind bin/ordexgoldd

# Rebuild (auto-downloads new versions)
docker compose build --no-cache

# Start
docker compose up -d
```

### Rebuild Without Cache

```bash
docker compose build --no-cache
```

### View Disk Usage

```bash
docker exec ordexwallet df -h
docker exec ordexwallet du -sh /data/*
```

## Security Operations

### Rotate RPC Credentials

```bash
# Generate new credentials (via UI or API)
# Delete old config
docker exec ordexwallet rm /data/config/ordexcoind.conf /data/config/ordexgoldd.conf

# Restart (generates new credentials)
docker compose restart
```

### Change Wallet Passphrase

Via UI: Wallet > Backup/Restore > Change Passphrase

Or via RPC:
```json
{
  "jsonrpc": "1.0",
  "id": "1",
  "method": "walletpassphrasechange",
  "params": ["oldpassphrase", "newpassphrase"]
}
```

## Health Checks

### Automated Health Check

```bash
# Check Flask is responding
curl http://localhost:15000/api/system/health

# Expected response:
# {"status": "ok", "daemons": {"ordexcoind": "connected", "ordexgoldd": "connected"}}
```

### Manual Health Check Script

```bash
#!/bin/bash
HEALTH=$(curl -s http://localhost:15000/api/system/health)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
  echo "OK"
else
  echo "UNHEALTHY: $HEALTH"
  exit 1
fi
```

## Performance Tuning

### Recommended Production Settings

In `ordexcoind.conf` / `ordexgoldd.conf`:
```
# Reduce memory usage
dbcache=512
maxconnections=16

# Reduce disk I/O
maxmempool=200

# Ensure adequate disk space
minchainfreespace=5000
```

### Monitoring Prometheus Metrics

Add to config:
```
metrics=1
prometheusport=19112
```

Then scrape `http://localhost:19112/metrics`

## Emergency Procedures

### Complete Data Loss

1. Stop container
2. Preserve `/data/config/` (contains RPC credentials)
3. Delete blockchain data
4. Start container - will resync

### Corrupt Database

```bash
docker compose down
docker volume rm ordexwallet_ordexwallet_data
docker compose up -d
```

Warning: This deletes all wallet data including private keys. Ensure you have backup.

### Container Crash Loop

1. Check logs for specific error
2. Verify volume mounts
3. Check disk space
4. Verify daemon binaries are executable