# BuildWise Server Starter für Windows PowerShell
# Startet den FastAPI-Server mit Fehlerbehandlung

Write-Host "🏗️  BuildWise Server Starter" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Prüfe Python-Installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python nicht gefunden. Bitte installieren Sie Python 3.8+" -ForegroundColor Red
    exit 1
}

# Prüfe und installiere Abhängigkeiten
Write-Host "📦 Prüfe Abhängigkeiten..." -ForegroundColor Yellow

$requiredPackages = @(
    "fastapi",
    "uvicorn[standard]",
    "sqlalchemy",
    "aiosqlite",
    "python-dotenv"
)

foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" 2>$null
        Write-Host "✅ $package ist installiert" -ForegroundColor Green
    } catch {
        Write-Host "❌ $package fehlt - installiere..." -ForegroundColor Yellow
        try {
            python -m pip install $package
            Write-Host "✅ $package installiert" -ForegroundColor Green
        } catch {
            Write-Host "❌ Fehler beim Installieren von $package" -ForegroundColor Red
        }
    }
}

# Server-Konfiguration
$host = "0.0.0.0"
$port = 8000

Write-Host "🚀 Starte BuildWise Server..." -ForegroundColor Green
Write-Host "🌐 Server wird gestartet auf http://$host`:$port" -ForegroundColor Cyan
Write-Host "📚 API-Dokumentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🏥 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "⏹️  Drücken Sie Ctrl+C zum Beenden" -ForegroundColor Yellow
Write-Host "-" * 50 -ForegroundColor Gray

try {
    # Starte den Server
    python -m uvicorn app.main:app --host $host --port $port --reload --log-level info
} catch {
    Write-Host "❌ Server-Fehler: $_" -ForegroundColor Red
    exit 1
} 