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

# Note: Storage directories will be created at runtime in start.sh
# /var/data is read-only during build phase

# Note: Database migrations are run in start.sh after DATABASE_URL is available
echo "[INFO] Build phase complete - migrations will run at startup"

echo "========================================"
echo "BuildWise Build - Complete"
echo "========================================"

