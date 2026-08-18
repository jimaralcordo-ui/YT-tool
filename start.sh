#!/bin/bash

set -e

echo "========================================"
echo "Starting bgutil POT server..."
echo "========================================"

cd bgutil-ytdlp-pot-provider/server

node build/main.js > /tmp/bgutil.log 2>&1 &

BGUTIL_PID=$!

cd ../..

echo "BGUTIL PID: $BGUTIL_PID"
echo "Waiting for bgutil..."

sleep 5

echo "========================================"
echo "BGUTIL LOG"
echo "========================================"

cat /tmp/bgutil.log || true

echo "========================================"
echo "Starting Flask with Gunicorn..."
echo "========================================"

exec gunicorn app:app \
    --bind 0.0.0.0:${PORT} \
    --workers 1 \
    --timeout 300