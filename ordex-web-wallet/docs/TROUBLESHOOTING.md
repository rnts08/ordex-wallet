# Ordex Web Wallet - Troubleshooting

## Common Issues

### Service Won't Start

#### Symptom
```
docker-compose up -d
# Container exits immediately or shows error
```

#### Diagnosis
```bash
# Check logs
docker logs ordex-web-wallet

# Check port conflicts
netstat -tlnp | grep 15000

# Check resource limits
docker system df
```

#### Solutions

1. **Port in use**
   ```bash
   # Find and stop conflicting service
   lsof -i :15000
   # Or change port in docker-compose.yml
   ```

2. **Missing environment**
   ```bash
   # Verify .env exists
   cat docker/.env
   ```

3. **Permission denied**
   ```bash
   # Fix volume permissions
   sudo chown -R 1000:1000 ./data
   ```

### Database Connection Failed

#### Symptom
```
psycopg2.OperationalError: could not connect to server
```

#### Diagnosis
```bash
docker logs ordex-web-wallet-postgres
docker exec ordex-web-wallet-postgres pg_isready
```

#### Solutions

1. **Postgres not ready**
   ```bash
   # Wait for health check or start manually
   docker-compose up -d postgres
   sleep 10
   docker-compose up -d
   ```

2. **Wrong credentials**
   ```bash
   # Verify .env matches postgres env
   ```

3. **Volume corruption**
   ```bash
   # Remove and recreate (DANGER: loses data)
   docker-compose down -v
   docker-compose up -d
   ```

### RPC Connection Failed

#### Symptom
```
RPC Error: could not connect to server
```

#### Diagnosis
```bash
docker logs ordex-web-wallet-ordexcoind
curl http://localhost:5332
```

#### Solutions

1. **Daemon not ready**
   ```bash
   docker-compose up -d ordexcoind
   sleep 30
   docker-compose up -d webwallet
   ```

2. **Wrong RPC password**
   ```bash
   # Verify RPC_PASS in .env matches daemon config
   ```

3. **Network issue**
   ```yaml
   # Check docker-compose.yml networks
   webwallet:
     networks:
       - webwallet_network
   ordexcoind:
     networks:
       - webwallet_network
   ```

### Wallet Creation Failed

#### Symptom
```
Error: Failed to create wallets
```

#### Diagnosis
```bash
docker logs ordex-web-wallet | grep -i wallet
docker exec ordex-web-wallet ordexcoin-cli listwallets
```

#### Solutions

1. **Wallet directory**
   ```bash
   # Verify volume mounted
   docker exec ordex-web-wallet ls -la /data/wallets/
   ```

2. **Permission**
   ```bash
   docker exec ordex-web-wallet chown -R 1000:1000 /data/wallets
   ```

3. **Corrupted wallet**
   ```bash
   # Manual recovery
   docker exec ordex-web-wallet ordexcoind -walletdir=/data/wallets listwallets
   ```

### Authentication Failed

#### Symptom
```
Invalid credentials
```

#### Solutions

1. **Check user exists**
   ```bash
   docker exec ordex-web-wallet python -c "
   from database import get_user_by_username
   print(get_user_by_username('admin'))
   "
   ```

2. **Reset password**
   ```python
   # Via Python
   import bcrypt
   hash = bcrypt.hashpw(b'newpassword', bcrypt.gensalt())
   # Update directly in database
   ```

### Slow Performance

#### Diagnosis
```bash
docker stats --no-stream

# Check database queries
docker exec ordex-web-wallet python -c "
from database import DATABASE
print(DATABASE.execute_one('SELECT pg_stat_activity WHERE state != \\'idle\\''))
"
```

#### Solutions

1. **Increase memory**
   ```yaml
   # docker-compose.yml
   postgres:
     deploy:
       resources:
         limits:
           memory: 1G
   ```

2. **Optimize queries**
   ```sql
   -- Add indexes
   CREATE INDEX idx_sessions_expires ON sessions(expires_at);
   ```

3. **Connection pooling**
   ```python
   # Adjust in database connection
   ```

### High Memory Usage (Daemon)

#### Symptom
```
Error: out of memory
```

#### Solutions

1. **Reduce cache**
   ```yaml
   ordexcoind:
     command: ordexcoind -server ... -maxmempool=100
   ```

2. **Enable pruning**
   ```yaml
   command: ordexcoind ... -prune=500
   ```

### Admin Can't Access

#### Symptom
```
Admin access required
```

#### Solutions

1. **Check is_admin flag**
   ```bash
   docker exec ordex-web-wallet python -c "
   from database import get_user_by_username
   user = get_user_by_username('admin')
   print(user['is_admin'] if user else 'Not found')
   "
   ```

2. **Set admin flag**
   ```bash
   docker exec ordex-web-wallet python -c "
   from database import DATABASE
   DATABASE.execute_write(\"UPDATE users SET is_admin=True WHERE username='admin'\")
   "
   ```

### Session Expired

#### Symptom
```
Invalid or expired session
```

#### Solutions

1. **Clear browser storage**
   ```javascript
   localStorage.clear()
   ```

2. **Extend session duration**
   ```bash
   # In .env
   SESSION_DURATION=604800  # 7 days
   ```

## Debug Mode

### Enable Debug Logging

```bash
# In .env
FLASK_ENV=development

# Or in code
app.logger.setLevel(10)
```

### Python Debug Shell

```bash
docker exec -it ordex-web-wallet python
>>> from app import create_app
>>> app = create_app()
>>> app.debug = True
```

## Recovery Procedures

### Full System Reset

```bash
# WARNING: Loses all data
docker-compose down -v
rm -rf ./data
docker-compose up -d

# Recreate admin
docker exec ordex-web-wallet python -m scripts.init_admin \
    --username admin --password "newpassword"
```

### Wallet Recovery

```bash
# From backup
docker cp ./backup/wallets ordex-web-wallet:/data/
docker exec ordex-web-wallet chown -R 1000:1000 /data/wallets
docker-compose restart
```

## Getting Help

1. Check logs first
2. Verify service dependencies
3. Check Docker/network configuration
4. Test individual components
5. Review documentation in docs/

## Log Patterns

| Pattern | Likely Cause |
|---------|--------------|
| `could not connect` | Service down |
| `authentication` | Cred mismatch |
| `out of memory` | Resource limits |
| `database locked` | Concurrent access |
| `wallet not found` | Wrong wallet name |