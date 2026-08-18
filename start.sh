#!/bin/bash

set -e

echo "========================================"
echo "Starting bgutil POT server..."
echo "========================================"

cd /app/bgutil-ytdlp-pot-provider/server

node build/main.js > /tmp/bgutil.log 2>&1 &

BGUTIL_PID=$!

echo "BGUTIL PID: $BGUTIL_PID"

cd /app

echo "Waiting for bgutil server on port 4416..."

for i in {1..30}; do

    if curl -s http://127.0.0.1:4416/ > /dev/null 2>&1; then
        echo "BGUTIL server is ready!"
        break
    fi

    if ! kill -0 "$BGUTIL_PID" 2>/dev/null; then
        echo "BGUTIL server stopped unexpectedly."
        echo "========================================"
        cat /tmp/bgutil.log || true
        echo "========================================"
        exit 1
    fi

    echo "Waiting... ($i/30)"
    sleep 1

done

if ! kill -0 "$BGUTIL_PID" 2>/dev/null; then
    echo "BGUTIL failed to start."
    cat /tmp/bgutil.log || true
    exit 1
fi

echo "========================================"
echo "BGUTIL LOG"
echo "========================================"

cat /tmp/bgutil.log || true

echo "========================================"
echo "Starting Flask / Gunicorn..."
echo "========================================"

exec gunicorn app:app \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 1 \
    --timeout 300