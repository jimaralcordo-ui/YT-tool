#!/bin/bash

set -e

echo "Starting bgutil POT server..."

cd bgutil-ytdlp-pot-provider/server

node build/main.js > /tmp/bgutil.log 2>&1 &

cd ../..

echo "Waiting for bgutil..."

sleep 5

echo "Starting Flask..."

exec gunicorn app:app --bind 0.0.0.0:${PORT}