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

echo "Initializing database..."
python -c "
import os
import sys
sys.path.insert(0, '/app')
os.environ.setdefault('DATABASE_URL', os.environ.get('DATABASE_URL', os.environ.get('DATABASE_URL', 'postgresql://webwallet:password@postgres:5432/webwallet')))
os.environ.setdefault('RPC_PASS', os.environ.get('RPC_PASS', 'dummy'))
from ordex_web_wallet.database import init_database
init_database()
print('Database ready')
"

exec "$@"