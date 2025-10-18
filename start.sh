#!/usr/bin/env bash
# BuildWise Start Script for Render.com
# Starts the application with Gunicorn + Uvicorn workers for production

set -o errexit  # Exit on error
set -o pipefail # Exit on pipe failure
set -o nounset  # Exit on undefined variable

echo "========================================"
echo "BuildWise Start Script - Production"
echo "========================================"

# Display environment info
echo "[INFO] Environment: ${ENVIRONMENT:-not set}"
echo "[INFO] Python version: $(python --version)"

# Check database connection
echo "[INFO] Checking database connection..."
if [ -z "${DATABASE_URL:-}" ]; then
    echo "[ERROR] DATABASE_URL is not set!"
    exit 1
else
    echo "[SUCCESS] DATABASE_URL is configured"
fi

# Ensure storage directories exist
echo "[INFO] Creating storage directories..."
mkdir -p /var/data/storage/uploads
mkdir -p /var/data/storage/pdfs/invoices
mkdir -p /var/data/storage/temp
mkdir -p /var/data/storage/cache
mkdir -p /var/data/storage/company_logos
chmod -R 755 /var/data/storage
echo "[SUCCESS] Storage directories created"

# Run database migrations
echo "[INFO] Running database migrations..."
alembic upgrade head
echo "[SUCCESS] Database migrations completed"

# Calculate optimal worker count based on CPU cores
# Formula: (2 x $num_cores) + 1
# Render Starter: 0.5 CPU -> 2 workers
# Render Standard: 1 CPU -> 3 workers
# Render Pro: 2 CPU -> 5 workers
if [ -n "${GUNICORN_WORKERS:-}" ] && [ "${GUNICORN_WORKERS}" != "auto" ]; then
    WORKERS=${GUNICORN_WORKERS}
else
    # Try to detect CPU count
    if command -v nproc &> /dev/null; then
        CPU_CORES=$(nproc)
    else
        # Fallback if nproc not available
        CPU_CORES=1
    fi
    
    # Calculate workers: (2 × cores) + 1, minimum 2
    WORKERS=$((2 * CPU_CORES + 1))
    if [ ${WORKERS} -lt 2 ]; then
        WORKERS=2
    fi
fi

echo "[INFO] Starting with ${WORKERS} workers for optimal multi-user performance"

# Gunicorn configuration
TIMEOUT=${GUNICORN_TIMEOUT:-120}
GRACEFUL_TIMEOUT=${GUNICORN_GRACEFUL_TIMEOUT:-30}
KEEPALIVE=${GUNICORN_KEEPALIVE:-5}
MAX_REQUESTS=${GUNICORN_MAX_REQUESTS:-1000}
MAX_REQUESTS_JITTER=${GUNICORN_MAX_REQUESTS_JITTER:-50}
WORKER_CLASS=${GUNICORN_WORKER_CLASS:-uvicorn.workers.UvicornWorker}
WORKER_CONNECTIONS=${GUNICORN_WORKER_CONNECTIONS:-1000}
BIND_ADDRESS="0.0.0.0:${PORT:-8000}"

echo "[INFO] Configuration:"
echo "  - Workers: ${WORKERS}"
echo "  - Worker class: ${WORKER_CLASS}"
echo "  - Worker connections: ${WORKER_CONNECTIONS}"
echo "  - Timeout: ${TIMEOUT}s"
echo "  - Graceful timeout: ${GRACEFUL_TIMEOUT}s"
echo "  - Keep-alive: ${KEEPALIVE}s"
echo "  - Max requests: ${MAX_REQUESTS}"
echo "  - Bind address: ${BIND_ADDRESS}"

echo "========================================"
echo "Starting BuildWise with Gunicorn..."
echo "========================================"

# Start Gunicorn with Uvicorn workers
exec gunicorn app.main:app \
  --workers ${WORKERS} \
  --worker-class ${WORKER_CLASS} \
  --worker-connections ${WORKER_CONNECTIONS} \
  --bind ${BIND_ADDRESS} \
  --timeout ${TIMEOUT} \
  --graceful-timeout ${GRACEFUL_TIMEOUT} \
  --keep-alive ${KEEPALIVE} \
  --max-requests ${MAX_REQUESTS} \
  --max-requests-jitter ${MAX_REQUESTS_JITTER} \
  --preload \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --capture-output \
  --enable-stdio-inheritance

