# 🚀 BuildWise Server Start-Anleitung

## Problem: localhost:8000 startet nicht mehr

### 🔧 Schnelle Lösungen

#### **Option 1: Batch-Datei verwenden (Empfohlen für Windows)**
```bash
# Doppelklick auf die Datei oder im Terminal:
start_server.bat
```

#### **Option 2: PowerShell-Skript verwenden**
```powershell
# Im PowerShell-Terminal:
.\start_server.ps1
```

#### **Option 3: Python-Skript verwenden**
```bash
# Im Terminal:
python start_server.py
```

### 🔍 Manuelle Fehlerbehebung

#### **1. Prüfe Python-Installation**
```bash
python --version
# Sollte Python 3.8+ anzeigen
```

#### **2. Installiere fehlende Abhängigkeiten**
```bash
pip install fastapi uvicorn[standard] sqlalchemy aiosqlite python-dotenv
```

#### **3. Prüfe Port-Verfügbarkeit**
```powershell
# In PowerShell:
netstat -ano | findstr :8000
# Falls Port belegt, beende den Prozess oder ändere den Port
```

#### **4. Starte Server manuell**
```bash
cd BuildWise
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 🐛 Häufige Probleme und Lösungen

#### **Problem: "ModuleNotFoundError: No module named 'aiosqlite'"**
```bash
pip install aiosqlite==0.19.0
```

#### **Problem: "Port 8000 is already in use"**
```powershell
# Finde Prozess auf Port 8000
netstat -ano | findstr :8000

# Beende Prozess (ersetze PID mit der tatsächlichen Prozess-ID)
taskkill /PID <PID> /F
```

#### **Problem: "Permission denied"**
```bash
# Führe als Administrator aus oder ändere Port
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

#### **Problem: "Database connection failed"**
```bash
# Prüfe SQLite-Datei
ls -la buildwise.db

# Falls Datei beschädigt, lösche und erstelle neu
rm buildwise.db
python -c "from app.core.database import engine; import asyncio; asyncio.run(engine.dispose())"
```

### 📋 Server-Status prüfen

#### **Health Check**
```bash
curl http://localhost:8000/health
# Sollte {"status": "healthy"} zurückgeben
```

#### **API-Dokumentation**
```
http://localhost:8000/docs
```

#### **Root-Endpoint**
```bash
curl http://localhost:8000/
```

### 🔧 Erweiterte Konfiguration

#### **Umgebungsvariablen (.env)**
```env
# Server-Konfiguration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Datenbank-Konfiguration
DATABASE_URL=sqlite+aiosqlite:///./buildwise.db

# CORS-Konfiguration
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### **Alternative Ports**
```bash
# Port 8001 verwenden
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Port 3000 verwenden
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### 📊 Debugging

#### **Detaillierte Logs aktivieren**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

#### **Server-Status überwachen**
```bash
# In separatem Terminal
watch -n 1 "curl -s http://localhost:8000/health"
```

### 🆘 Support

Falls keine der Lösungen funktioniert:

1. **Prüfe die Logs**: Schauen Sie in die Terminal-Ausgabe für Fehlermeldungen
2. **Prüfe die Abhängigkeiten**: `pip list | grep -E "(fastapi|uvicorn|sqlalchemy)"`
3. **Prüfe die Python-Version**: `python --version`
4. **Prüfe die Verzeichnisstruktur**: Stellen Sie sicher, dass Sie im BuildWise-Verzeichnis sind

### ✅ Erfolgreicher Start

Wenn der Server erfolgreich startet, sollten Sie folgende Ausgabe sehen:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [PID] using StatReload
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 🌐 Zugriff auf den Server

- **API-Dokumentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root-Endpoint**: http://localhost:8000/
- **Frontend**: http://localhost:5173 (Vite Dev Server) 