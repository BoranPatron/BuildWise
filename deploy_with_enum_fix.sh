#!/bin/bash
# Deployment-Script für BuildWise mit atomarer Enum-Migration

echo "🚀 Starting BuildWise deployment with atomic enum migration..."

# 1. Atomare Enum-Migration durchführen
echo "📊 Running atomic enum migration..."
python fix_enum_atomic.py

if [ $? -ne 0 ]; then
    echo "❌ Enum migration failed. Aborting deployment."
    exit 1
fi

echo "✅ Enum migration completed successfully!"

# 2. Backend starten
echo "🔧 Starting backend server..."
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# 3. Frontend starten (falls gewünscht)
echo "🎨 Frontend is ready to be started separately"
echo "   Run: cd Frontend/Frontend && npm start"

echo "🎉 Deployment completed successfully!"
echo "   Backend: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
