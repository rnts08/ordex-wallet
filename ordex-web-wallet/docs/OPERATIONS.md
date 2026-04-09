# Ordex Web Wallet - Operations

## Deployment

### Initial Setup

```bash
# 1. Clone and navigate
cd ordex-web-wallet

# 2. Configure environment
cp docker/.env.example docker/.env
# Edit with strong passwords

# 3. Build and start
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d

# 4. Verify services
docker-compose ps
# Database tables are auto-created on first start
# Migrations run automatically on every startup

# 5. (Optional) Initialize admin - can be done anytime
docker exec ordex-web-wallet python -m scripts.init_admin \
    --username admin --password "YourSecurePassword"
```

### Database Auto-Initialization

The system automatically:
- Creates the PostgreSQL database (if not exists)
- Runs `schema_migrations` table
- Applies all schema changes (idempotent)
- Runs on every container startup

```bash
# Verify database is ready
docker logs ordex-web-wallet | grep "Database"
# Output: "Database initialized" or "Applying migration v1..."

# Manual migration check
docker exec ordex-web-wallet python -c "
from ordex_web_wallet.database import get_schema_version
print(f'Schema version: {get_schema_version()}')
"
```

### Production Deployment

```bash
# 1. Use production image
# Build locally or use CI/CD pipeline

# 2. Set production environment
export FLASK_ENV=production
export SESSION_DURATION=86400

# 3. Start with production settings
docker-compose -f docker/docker-compose.yml up -d

# 4. Configure reverse proxy (nginx)
# Proxy port 15000 to 80/443
```

## Backup & Restore

### Database Backup

```bash
# Manual backup
docker exec ordex-web-wallet-postgres pg_dump -U webwallet webwallet > backup.sql

# Automated backup ( cron )
0 2 * * * docker exec ordex-web-wallet-postgres pg_dump -U webwallet webwallet | gzip > /backups/db-$(date +\%Y\%m\%d).sql.gz
```

### Wallet Backup

```bash
# Export specific user wallet
docker exec ordex-web-wallet ordexcoin-cli -rpcwallet=wallet_{user_id}_ordexcoin backupwallet /data/backups/user_{user_id}_oxc.dat
docker exec ordex-web-wallet ordexgold-cli -rpcwallet=wallet_{user_id}_ordexgold backupwallet /data/backups/user_{user_id}_oxg.dat

# Via API
curl -X POST http://localhost:15000/api/backup/create \
    -H "Authorization: Bearer $TOKEN"
```

### Full System Backup

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/$DATE"

mkdir -p $BACKUP_DIR

# Database
docker exec ordex-web-wallet-postgres pg_dump -U webwallet webwallet > $BACKUP_DIR/database.sql

# Wallets
docker cp ordex-web-wallet:/data/wallets $BACKUP_DIR/

# Config
cp docker/.env $BACKUP_DIR/.env (exclude secrets)

echo "Backup complete: $BACKUP_DIR"
```

### Restore

```bash
# Database
docker exec -i ordex-web-wallet-postgres psql -U webwallet webwallet < backup.sql

# Wallets
docker cp ./wallets ordex-web-wallet:/data/

# Restart services
docker-compose restart
```

## Monitoring

### Health Checks

```bash
# Service health
curl http://localhost:15000/api/system/health

# Database
docker exec ordex-web-wallet-postgres pg_isready

# Daemons
curl http://localhost:5332
curl http://localhost:5333
```

### Metrics

```bash
# Prometheus format
curl http://localhost:15000/api/system/metrics

# Custom metrics in Prometheus:
# - ordexweb_users_total
# - ordexweb_active_sessions
# - ordexweb_wallet_balance_total
```

### Logs

```bash
# Application logs
docker logs ordex-web-wallet --follow

# Per service
docker logs ordex-web-wallet-postgres --follow
docker logs ordex-web-wallet-ordexcoind --follow
docker logs ordex-web-wallet-ordexgoldd --follow

# Search logs
docker logs ordex-web-wallet 2>&1 | grep ERROR
```

### Resource Usage

```bash
docker stats --no-stream

# Expected ranges:
# - webwallet: ~100-200MB RAM
# - postgres: ~200-500MB RAM  
# - ordexcoind: 512MB-2GB RAM (sync state)
# - ordexgoldd: 512MB-2GB RAM
```

## Scaling

### Vertical Scaling

```bash
# Increase memory limits in docker-compose.yml
ordexcoind:
    mem_limit: 4g
    mem_reservation: 1g
```

### Horizontal Scaling (Future)

- Load balancer for multiple webwallet instances
- PostgreSQL read replicas
- Shared wallet storage (NFS)
- Background job queue (Redis)

## User Management

### Create Admin User

```bash
docker exec ordex-web-wallet python -m scripts.init_admin \
    --username admin --password "password" --email "admin@example.com"
```

### Disable User

```bash
curl -X POST http://localhost:15000/api/admin/users/123/disable \
    -H "Authorization: Bearer $ADMIN_TOKEN"
```

### View All Users

```bash
curl http://localhost:15000/api/admin/users \
    -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Maintenance

### Update Application

```bash
# Pull new image or rebuild
docker build -t rnts08/ordex-web-wallet:latest .

# Update
docker-compose -f docker/docker-compose.yml up -d --build

# Verify
curl http://localhost:15000/api/system/health
```

### Database Maintenance

```bash
# Vacuum (cleanup)
docker exec ordex-web-wallet-postgres psql -U webwallet webwallet -c "VACUUM ANALYZE;"

# Check connections
docker exec ordex-web-wallet-postgres psql -U webwallet webwallet -c "SELECT * FROM pg_stat_activity;"
```

### Log Rotation

```bash
# Application logs rotate via entrypoint.sh (10MB max, 5 files)

# Docker logs
docker logs --rotate
# Or configure in daemon.json
```

## Security

### Key Rotation

```bash
# Rotate Flask secret
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
# Update .env and restart

# Rotate RPC password
# Update .env, update ordexcoin.conf, restart daemons
```

### SSL/TLS

```bash
# Via reverse proxy (nginx/caddy)
# Or use Docker with let's encrypt
```

### Firewall

```bash
# Only expose web port
ufw allow 15000/tcp

# Internal ports (5432, 5332, 5333) should not be exposed
```

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## Checklist

- [ ] Initial admin created
- [ ] Backups configured
- [ ] Monitoring alerts set
- [ ] Log rotation configured
- [ ] SSL/TLS configured
- [ ] Firewall configured
- [ ] Backup restore tested