#!/bin/bash

# BuildWise API Start Script
# This script handles both local development and production deployment
# Enhanced with health checks, dependency verification, and graceful shutdown

echo "🏗️  BuildWise Backend - Enhanced Start"
echo "========================================"

# Function to handle graceful shutdown
cleanup() {
    echo "🛑 Graceful shutdown initiated..."
    if [ ! -z "$GUNICORN_PID" ]; then
        echo "📡 Sending SIGTERM to Gunicorn (PID: $GUNICORN_PID)"
        kill -TERM "$GUNICORN_PID" 2>/dev/null
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 "$GUNICORN_PID" 2>/dev/null; then
                echo "✅ Server gracefully stopped"
                break
            fi
            echo "⏳ Waiting for graceful shutdown... ($i/10)"
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 "$GUNICORN_PID" 2>/dev/null; then
            echo "⚠️  Force killing server..."
            kill -KILL "$GUNICORN_PID" 2>/dev/null
        fi
    fi
    echo "👋 BuildWise Backend stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Function to check dependencies
check_dependencies() {
    echo "📦 Checking dependencies..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found!"
        return 1
    fi
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 not found!"
        return 1
    fi
    
    # Check if main dependencies are installed
    local missing_deps=()
    
    if ! python3 -c "import fastapi" 2>/dev/null; then
        missing_deps+=("fastapi")
    fi
    
    if ! python3 -c "import uvicorn" 2>/dev/null; then
        missing_deps+=("uvicorn")
    fi
    
    if ! python3 -c "import gunicorn" 2>/dev/null; then
        missing_deps+=("gunicorn")
    fi
    
    if ! python3 -c "import sqlalchemy" 2>/dev/null; then
        missing_deps+=("sqlalchemy")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "⚠️  Missing dependencies: ${missing_deps[*]}"
        echo "📦 Installing missing dependencies..."
        
        if pip3 install "${missing_deps[@]}" --quiet; then
            echo "✅ Dependencies installed successfully"
        else
            echo "❌ Failed to install dependencies"
            return 1
        fi
    else
        echo "✅ All dependencies are available"
    fi
    
    return 0
}

# Function to check database
check_database() {
    echo "🗄️  Checking database..."
    
    if [ -f "buildwise.db" ]; then
        echo "✅ Database file found"
    else
        echo "⚠️  Database file not found - will be created on first run"
    fi
    
    return 0
}

# Function to perform health check
health_check() {
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for server to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:${PORT}/health" > /dev/null 2>&1; then
            echo "✅ Server is healthy and ready!"
            return 0
        fi
        
        echo "⏳ Health check attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ Health check failed after $max_attempts attempts"
    return 1
}

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

# Perform pre-start checks
if ! check_dependencies; then
    echo "❌ Dependency check failed"
    exit 1
fi

if ! check_database; then
    echo "⚠️  Database check completed with warnings"
fi

# Start Gunicorn with the configuration file
echo "🚀 Starting Gunicorn server..."

# Start Gunicorn in background to capture PID
gunicorn app.main:app \
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
    --log-level info &
    
GUNICORN_PID=$!
echo "📡 Gunicorn started with PID: $GUNICORN_PID"

# Perform health check
if health_check; then
    echo "✅ BuildWise Backend is ready!"
    echo "🌐 Backend: http://localhost:$PORT"
    echo "📚 API Docs: http://localhost:$PORT/docs"
    echo "💡 Press Ctrl+C to stop the server"
    
    # Wait for the Gunicorn process
    wait $GUNICORN_PID
else
    echo "❌ Server failed to start properly"
    cleanup
    exit 1
fi