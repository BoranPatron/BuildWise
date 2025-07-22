@echo off
echo 🏗️  BuildWise Server Starter
echo ==================================================

echo 📦 Prüfe Abhängigkeiten...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo ❌ FastAPI fehlt - installiere...
    python -m pip install fastapi uvicorn[standard] sqlalchemy aiosqlite python-dotenv
)

echo 🚀 Starte BuildWise Server...
echo 🌐 Server wird gestartet auf http://localhost:8000
echo 📚 API-Dokumentation: http://localhost:8000/docs
echo 🏥 Health Check: http://localhost:8000/health
echo ⏹️  Drücken Sie Ctrl+C zum Beenden
echo --------------------------------------------------

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause 