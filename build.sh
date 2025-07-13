#!/bin/bash

# BuildWise Deployment Script for Render.com
# Ensures Python 3.13 compatibility

echo "🔧 BuildWise Deployment Script"
echo "Python Version: $(python --version)"
echo "Pip Version: $(pip --version)"

# Clear any existing cache
echo "🧹 Clearing pip cache..."
pip cache purge

# Upgrade pip to latest version
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements with force reinstall
echo "📦 Installing requirements..."
pip install --no-cache-dir --force-reinstall -r requirements.txt

# Verify installations
echo "✅ Verifying installations..."
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')"
python -c "import uvicorn; print(f'Uvicorn: {uvicorn.__version__}')"
python -c "import psycopg2; print('Psycopg2: OK')"

echo "🚀 Build completed successfully!" 