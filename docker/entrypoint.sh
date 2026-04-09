#!/bin/bash
set -e

echo "=========================================="
echo "Starting OrdexWallet..."
echo "=========================================="

# All data stored in /data (blockchain, config, database, logs)
echo "Initializing data directories..."
mkdir -p /data/{config,blockchain/ordexcoin,blockchain/ordexgold,logs,backups}

# Verify daemon binaries are available
echo "Checking daemon binaries..."
ORDEXCOIND_AVAILABLE=false
ORDEXGOLDD_AVAILABLE=false

# Check in /data/bin first (volume mount)
if [ -f /data/bin/ordexcoind ] && [ -x /data/bin/ordexcoind ]; then
    cp /data/bin/ordexcoind /usr/local/bin/
    chmod +x /usr/local/bin/ordexcoind
    ORDEXCOIND_AVAILABLE=true
    echo "  ordexcoind: found in /data/bin"
elif [ -f /usr/local/bin/ordexcoind ] && [ -x /usr/local/bin/ordexcoind ]; then
    ORDEXCOIND_AVAILABLE=true
    echo "  ordexcoind: found in /usr/local/bin"
else
    echo "  ordexcoind: NOT FOUND - please ensure daemon binary is available"
fi

# Check ordexgoldd
if [ -f /data/bin/ordexgoldd ] && [ -x /data/bin/ordexgoldd ]; then
    cp /data/bin/ordexgoldd /usr/local/bin/
    chmod +x /usr/local/bin/ordexgoldd
    ORDEXGOLDD_AVAILABLE=true
    echo "  ordexgoldd: found in /data/bin"
elif [ -f /usr/local/bin/ordexgoldd ] && [ -x /usr/local/bin/ordexgoldd ]; then
    ORDEXGOLDD_AVAILABLE=true
    echo "  ordexgoldd: found in /usr/local/bin"
else
    echo "  ordexgoldd: NOT FOUND - please ensure daemon binary is available"
fi

# Exit if any daemon is missing
if [ "$ORDEXCOIND_AVAILABLE" = false ] || [ "$ORDEXGOLDD_AVAILABLE" = false ]; then
    echo "ERROR: One or more daemon binaries are missing. Exiting."
    exit 1
fi

# Generate configs if they don't exist (idempotent)
echo "Checking configuration files..."
if [ ! -f /data/config/ordexcoind.conf ] || [ ! -f /data/config/ordexgoldd.conf ]; then
    echo "Generating configuration files..."
    python -c "
import sys
sys.path.insert(0, '.')
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
echo "Waiting for daemons to initialize..."
sleep 5

# Verify daemons are running (using /proc check since pgrep may not be available)
echo "Verifying daemon processes..."
ORDEXCOIND_RUNNING=false
ORDEXGOLDD_RUNNING=false

if [ -d /proc ]; then
    for pid in /proc/[0-9]*; do
        if [ -f "$pid/comm" ]; then
            comm=$(cat "$pid/comm" 2>/dev/null)
            if [ "$comm" = "ordexcoind" ]; then
                ORDEXCOIND_RUNNING=true
            fi
            if [ "$comm" = "ordexgoldd" ]; then
                ORDEXGOLDD_RUNNING=true
            fi
        fi
    done
fi

if [ "$ORDEXCOIND_RUNNING" = false ]; then
    echo "WARNING: ordexcoind process not detected"
fi
if [ "$ORDEXGOLDD_RUNNING" = false ]; then
    echo "WARNING: ordexgoldd process not detected"
fi

# Start Flask
echo "Starting Flask application (daemons will sync in background)..."
python -c "import app; app.main()"