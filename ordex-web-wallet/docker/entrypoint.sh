#!/bin/bash
set -e

LOG_DIR="/data/logs"
LOG_FILE="$LOG_DIR/app.log"
MAX_SIZE=10485760
MAX_FILES=5

mkdir -p "$LOG_DIR"

log_rotate() {
    if [ -f "$LOG_FILE" ]; then
        SIZE=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$SIZE" -ge "$MAX_SIZE" ]; then
            for i in $(seq $((MAX_FILES - 1)) -1 1); do
                [ -f "$LOG_FILE.$i" ] && mv "$LOG_FILE.$i" "$LOG_FILE.$((i + 1))"
            done
            mv "$LOG_FILE" "$LOG_FILE.1"
            touch "$LOG_FILE"
        fi
    else
        touch "$LOG_FILE"
    fi
}

(while true; do
    sleep 300
    log_rotate
done) &

export PYTHONPATH="/app"

echo "Initializing database..."
python -c "
import os, sys
sys.path.insert(0, '/app')

# Ensure env vars are set for database
db_url = os.environ.get('DATABASE_URL', '')
rpc_pass = os.environ.get('RPC_PASS', '')

if db_url and rpc_pass:
    try:
        from ordex_web_wallet.database import init_database
        init_database()
        print('Database initialized')
    except Exception as e:
        print(f'Database init: {e}')
else:
    print('Skipping DB init - env not ready')
" || true

exec "$@"