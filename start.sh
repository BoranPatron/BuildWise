#!/bin/bash

# BuildWise API Start Script
# This script handles both local development and production deployment

echo "Starting BuildWise with Gunicorn..."
echo "========================================"

# Get port from environment variable (set by Render.com) or use default
PORT=${PORT:-8000}
echo "Using port: $PORT"

# Check if we're in production (Render.com sets this)
if [ -n "$RENDER" ]; then
    echo "Running in Render.com production environment"
    # Use production settings
    export WORKERS=${WORKERS:-2}
else
    echo "Running in development environment"
    # Use development settings
    export WORKERS=${WORKERS:-1}
fi

echo "Starting with $WORKERS workers on 0.0.0.0:$PORT"

# Start Gunicorn with the configuration file
exec gunicorn app.main:app \
    --config gunicorn.conf.py \
    --bind 0.0.0.0:$PORT \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info