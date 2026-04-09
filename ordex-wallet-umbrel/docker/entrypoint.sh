#!/bin/bash
set -e

echo "=========================================="
echo "Starting OrdexWallet..."
echo "=========================================="

# All data stored in /data (blockchain, config, database, logs)
echo "Initializing data directories..."
mkdir -p /data/{config,blockchain/ordexcoin,blockchain/ordexgold,logs,backups}

# Make daemon binaries available (handle both Umbriel volume mount and local install)
echo "Setting up daemon binaries..."
if [ -f /data/bin/ordexcoind ]; then
    cp /data/bin/ordexcoind /usr/local/bin/
    chmod +x /usr/local/bin/ordexcoind
fi
if [ -f /data/bin/ordexgoldd ]; then
    cp /data/bin/ordexgoldd /usr/local/bin/
    chmod +x /usr/local/bin/ordexgoldd
fi

# Generate configs if they don't exist (idempotent)
echo "Checking configuration files..."
if [ ! -f /data/config/ordexcoind.conf ] || [ ! -f /data/config/ordexgoldd.conf ]; then
    echo "Generating configuration files..."
    python -c "
import sys
sys.path.insert(0, '/app')
from config import ConfigGenerator
gen = ConfigGenerator('/data/config', '/data')
if gen.is_first_startup():
    gen.generate_all_configs()
    print('Configuration files generated.')
else:
    print('Configuration already exists.')
"
fi

# Start ordexcoind in daemon mode (background)
echo "Starting ordexcoind daemon..."
ordexcoind -daemon -datadir=/data/blockchain/ordexcoin -conf=/data/config/ordexcoind.conf || true

# Start ordexgoldd in daemon mode (background)
echo "Starting ordexgoldd daemon..."
ordexgoldd -daemon -datadir=/data/blockchain/ordexgold -conf=/data/config/ordexgoldd.conf || true

# Wait briefly for daemons to start accepting connections
sleep 5

# Start Flask
echo "Starting Flask application (daemons will sync in background)..."
cd /app
python -c "import app; app.main()"