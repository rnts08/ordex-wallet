#!/bin/bash
set -e

echo "=========================================="
echo "Starting OrdexWallet..."
echo "=========================================="

# Get user info for proper permissions (from docker-compose user or default)
if [ -n "$USER_ID" ]; then
    USE_USER=$USER_ID
    USE_GROUP=$GROUP_ID
else
    USE_USER=$(id -u)
    USE_GROUP=$(id -g)
fi
echo "Running with user ID: $USE_USER, group ID: $USE_GROUP"

# All data stored in /data (blockchain, config, database, logs)
echo "Initializing data directories..."
mkdir -p /data/{config,blockchain/ordexcoin,blockchain/ordexgold,logs,backups}

# Ensure proper ownership for the running user
echo "Setting directory ownership to $USE_USER:$USE_GROUP..."
chown -R $USE_USER:$USE_GROUP /data 2>/dev/null || true

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

# Ensure config files have proper permissions
chown $USE_USER:$USE_GROUP /data/config/*.conf 2>/dev/null || true
chmod 600 /data/config/*.conf 2>/dev/null || true

# Setup log rotation
echo "Setting up log rotation..."
LOG_DIR="/data/logs"
MAX_LOG_SIZE=10485760  # 10MB
MAX_LOG_FILES=5

# Create log rotation function
rotate_logs() {
    local log_file=$1
    local max_size=$2
    local max_files=$3
    
    if [ -f "$log_file" ]; then
        local size=$(stat -c%s "$log_file" 2>/dev/null || echo 0)
        if [ "$size" -gt "$max_size" ]; then
            # Rotate logs
            for i in $(seq $((max_files - 1)) -1 1); do
                if [ -f "${log_file}.$i" ]; then
                    mv "${log_file}.$i" "${log_file}.$((i + 1))"
                fi
            done
            mv "$log_file" "${log_file}.1"
            touch "$log_file"
            chown $USE_USER:$USE_GROUP "$log_file" 2>/dev/null || true
        fi
    fi
}

# Rotate daemon logs
rotate_logs "$LOG_DIR/ordexcoind.log" $MAX_LOG_SIZE $MAX_LOG_FILES
rotate_logs "$LOG_DIR/ordexgoldd.log" $MAX_LOG_SIZE $MAX_LOG_FILES

# Create wrapper script for log rotation background task
cat > /tmp/rotate_logs.sh << 'ROTATE_EOF'
#!/bin/bash
LOG_DIR="/data/logs"
MAX_SIZE=10485760
MAX_FILES=5
INTERVAL=300  # Check every 5 minutes

while true; do
    for logfile in ordexcoind.log ordexgoldd.log; do
        if [ -f "$LOG_DIR/$logfile" ]; then
            size=$(stat -c%s "$LOG_DIR/$logfile" 2>/dev/null || echo 0)
            if [ "$size" -gt "$MAX_SIZE" ]; then
                for i in $(seq $((MAX_FILES - 1)) -1 1); do
                    [ -f "$LOG_DIR/$logfile.$i" ] && mv "$LOG_DIR/$logfile.$i" "$LOG_DIR/$logfile.$((i + 1))"
                done
                mv "$LOG_DIR/$logfile" "$LOG_DIR/$logfile.1"
                touch "$LOG_DIR/$logfile"
            fi
        fi
    done
    sleep $INTERVAL
done
ROTATE_EOF
chmod +x /tmp/rotate_logs.sh

# Start log rotation in background
nohup /tmp/rotate_logs.sh > /dev/null 2>&1 &

# Start ordexcoind in daemon mode (background)
echo "Starting ordexcoind daemon..."
ordexcoind -daemon -datadir=/data/blockchain/ordexcoin -conf=/data/config/ordexcoind.conf || true

# Start ordexgoldd in daemon mode (background)
echo "Starting ordexgoldd daemon..."
ordexgoldd -daemon -datadir=/data/blockchain/ordexgold -conf=/data/config/ordexgoldd.conf || true

# Wait for daemons to be ready before starting Flask
echo "Waiting for daemons to be ready..."
MAX_RETRIES=30
RETRY_DELAY=2

wait_for_daemon() {
    local daemon_name=$1
    local rpc_port=$2
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        # Use Python to check if port is open (more reliable than curl)
        if python3 -c "import socket; s=socket.socket(); s.settimeout(1); result=s.connect_ex(('127.0.0.1',$rpc_port)); s.close(); exit(0 if result==0 else 1)" 2>/dev/null; then
            echo "  $daemon_name: ready (port $rpc_port)"
            return 0
        fi
        retries=$((retries + 1))
        echo "  Waiting for $daemon_name... ($retries/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    done
    
    echo "  WARNING: $daemon_name may not be ready after $MAX_RETRIES attempts"
    return 1
}

# Wait for both daemons
wait_for_daemon "ordexcoind" "25173"
wait_for_daemon "ordexgoldd" "25466"

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