# OrdexWallet Docker Deployment Plan

## Overview
Dockerized deployment of OrdexWallet with Flask backend, frontend assets, and ordexnetwork daemons.

## Architecture Components

### 1. Services
- **ordexwallet-app**: Flask backend API serving REST endpoints
- **ordexcoind**: Ordex network daemon (main network)
- **ordexgoldd**: Ordex Gold network daemon (sidechain/testnet)
- **nginx** (optional): Reverse proxy for SSL termination and static file serving
- **redis** (optional): Caching layer for price data and session storage

### 2. Docker Compose Structure
```
version: '3.8'

services:
  app:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - RPC_USER=${RPC_USER}
      - RPC_PASSWORD=${RPC_PASSWORD}
      - ORDEXCOIND_RPC_PORT=...
      - ORDEXGOLDD_RPC_PORT=...
    volumes:
      - wallet_data:/wallet
      - config_data:/config
      - logs:/app/logs
    depends_on:
      - ordexcoind
      - ordexgoldd
    restart: unless-stopped

  ordexcoind:
    image: ordexnetwork/ordexcoind:latest
    ports:
      - "RPC_PORT:RPC_PORT"
      - "P2P_PORT:P2P_PORT"
    volumes:
      - ordexcoin_data:/root/.ordexcoin
    command: ["ordexcoind", "-printtoconsole", "-rpcallowip=::/0"]
    restart: unless-stopped

  ordexgoldd:
    image: ordexnetwork/ordexgoldd:latest
    ports:
      - "RPC_PORT:RPC_PORT"
      - "P2P_PORT:P2P_PORT"
    volumes:
      - ordexgold_data:/root/.ordexgold
    command: ["ordexgoldd", "-printtoconsole", "-rpcallowip=::/0"]
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  wallet_data:
  config_data:
  logs:
  ordexcoin_data:
  ordexgold_data:
```

## Detailed Service Plans

### 1. Flask Backend (app)
- **Dockerfile**: Based on python:3.9-slim
- Installs Python dependencies from requirements.txt
- Copies application code
- Sets up non-root user for security
- Exposes port 5000
- Uses gunicorn as WSGI server
- Health check endpoint: /api/system/health
- Environment variables for configuration
- Volumes for persistent wallet data, configs, and logs

### 2. Daemons (ordexcoind/ordexgoldd)
- Use official ordexnetwork images if available, otherwise build from source
- Configure RPC access with auto-generated credentials
- Set appropriate RPC allow-ips for internal network communication
- Persistent volume for blockchain data
- Expose RPC ports only to internal network (or bind to localhost)
- P2P ports exposed for network participation
- Proper daemon startup flags

### 3. Frontend/Nginx (optional)
- Serve static frontend files through nginx
- Optionally serve directly from Flask if preferred
- SSL termination with certificates
- Gzip compression
- Security headers
- Rate limiting
- Cache control for assets

### 4. Additional Services (Optional)
- **Redis**: For caching price data, news, and session storage
- **Prometheus + Grafana**: For monitoring
- **ELK Stack**: For log aggregation
- **Watchtower**: For automatic container updates

## Configuration Management

### Environment Variables
- `RPC_USER`: Username for daemon RPC access
- `RPC_PASSWORD`: Auto-generated secure password
- `FLASK_ENV`: development/production
- `SECRET_KEY`: Flask secret key for sessions
- Database connection strings (if using external DB)
- Exchange API keys for price data
- Backup encryption passphrase
- Email/SMTP settings for notifications

### Auto-generated Configs
On first startup:
1. Generate random RPC credentials for both daemons
2. Create daemon config files with appropriate settings
3. Initialize wallet directory structure
4. Set up backup cron job (via host or sidecar container)

## Data Persistence
- **Wallet Data**: Encrypted wallet files, keys, metadata
- **Blockchain Data**: Full node data for both networks
- **Configuration**: RPC settings, daemon configs, app settings
- **Logs**: Application and daemon logs
- **Backups**: Encrypted wallet backups

## Security Considerations
- Run containers as non-root users
- Restrict RPC access to internal Docker network
- Use Docker secrets for sensitive credentials (in production)
- Regular security scanning of images
- Read-only root filesystem where possible
- Limit container capabilities
- Use Docker content trust for image verification

## Networking
- Internal Docker network for service communication
- External ports only for necessary services (nginx ports 80/443)
- Daemon RPC ports bound to internal network only
- Optional: Separate networks for frontend/backend and daemon isolation

## Startup Sequence
1. Start ordexcoind and ordexgoldd containers
2. Wait for daemons to be ready (health checks)
3. Start Flask app container
4. Initialize configs and wallet if first run
5. Start nginx container (if used)
6. Begin background tasks (price fetching, backups, etc.)

## Monitoring and Maintenance
- Health checks for all services
- Log aggregation options
- Backup verification procedures
- Update strategy for containers and daemons
- Resource limits (memory, CPU)
- Pruning old blockchain data (if needed)