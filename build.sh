#!/usr/bin/env bash
# BuildWise Build Script for Render.com
# This script is executed during the build phase

set -o errexit  # Exit on error
set -o pipefail # Exit on pipe failure
set -o nounset  # Exit on undefined variable

echo "========================================"
echo "BuildWise Build Script - Starting"
echo "========================================"

# Display Python version
echo "[INFO] Python version:"
python --version

# Upgrade pip
echo "[INFO] Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "[INFO] Installing Python dependencies..."
pip install -r requirements.txt

# Display installed packages for debugging
echo "[INFO] Installed packages:"
pip list

# Create storage directory structure
echo "[INFO] Creating storage directory structure..."
mkdir -p /var/data/storage
mkdir -p /var/data/storage/uploads
mkdir -p /var/data/storage/pdfs
mkdir -p /var/data/storage/pdfs/invoices
mkdir -p /var/data/storage/temp
mkdir -p /var/data/storage/cache
mkdir -p /var/data/storage/company_logos

echo "[SUCCESS] Storage directories created at /var/data/storage"

# Set proper permissions
echo "[INFO] Setting storage permissions..."
chmod -R 755 /var/data/storage

# Check if DATABASE_URL is set
if [ -z "${DATABASE_URL:-}" ]; then
    echo "[WARNING] DATABASE_URL is not set - migrations will fail"
else
    echo "[INFO] DATABASE_URL is configured"
    
    # Run database migrations
    echo "[INFO] Running database migrations..."
    alembic upgrade head
    
    echo "[SUCCESS] Database migrations completed"
fi

echo "========================================"
echo "BuildWise Build - Complete"
echo "========================================"

