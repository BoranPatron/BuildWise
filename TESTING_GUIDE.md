# BuildWise Testing Guide - DSGVO-konforme Plattform

## 🚀 Schnellstart

### 1. Backend starten
```bash
# Im BuildWise-Verzeichnis
cd /c/Users/user/Documents/04_Repo/BuildWise

# Virtuelle Umgebung aktivieren (falls vorhanden)
# .venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Backend starten
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend starten
```bash
# Im Frontend-Verzeichnis
cd Frontend/Frontend

# Abhängigkeiten installieren (falls noch nicht geschehen)
npm install

# Frontend starten
npm run dev
```

### 3. System testen
```bash
# Im BuildWise-Verzeichnis
python test_gdpr_features.py
```

## 🔐 Admin-Zugang

### Admin-Benutzer
- **E-Mail**: admin@buildwise.de
- **Passwort**: admin123
- **Berechtigungen**: Vollzugriff auf alle Features

### Login im Frontend
1. Öffnen Sie http://localhost:5173
2. Klicken Sie auf "Login"
3. Geben Sie die Admin-Daten ein
4. Sie werden automatisch zum Dashboard weitergeleitet

## 📋 DSGVO-Features testen

### 1. Benutzerregistrierung mit DSGVO-Einwilligungen
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@buildwise.de",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "user_type": "private",
    "data_processing_consent": true,
    "marketing_consent": false,
    "privacy_policy_accepted": true,
    "terms_accepted": true
  }'
```

### 2. Login mit Einwilligungsprüfung
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@buildwise.de&password=SecurePassword123!"
```

### 3. DSGVO-Datenexport
```bash
# Zuerst Token erhalten (aus Login-Response)
TOKEN="your_jwt_token_here"

curl -X GET "http://localhost:8000/api/v1/gdpr/data-export" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Einwilligungsverwaltung
```bash
curl -X POST "http://localhost:8000/api/v1/gdpr/consent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "consent_type": "marketing",
    "granted": true
  }'
```

### 5. Datenlöschungsantrag
```bash
curl -X POST "http://localhost:8000/api/v1/gdpr/data-deletion-request" \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Datenschutzerklärung abrufen
```bash
curl -X GET "http://localhost:8000/api/v1/gdpr/privacy-policy"
```

## 🧪 Automatisierte Tests

### Vollständiger DSGVO-Test
```bash
python test_gdpr_features.py
```

### Einzelne Tests
```bash
# Nur Health Check
python -c "
import asyncio
from test_gdpr_features import GDPRFeatureTester
tester = GDPRFeatureTester()
asyncio.run(tester.test_health_check())
"

# Nur Passwort-Stärke-Validierung
python -c "
import asyncio
from test_gdpr_features import GDPRFeatureTester
tester = GDPRFeatureTester()
asyncio.run(tester.test_password_strength_validation())
"
```

## 🔍 API-Dokumentation

### Swagger UI
- **URL**: http://localhost:8000/docs
- **Features**: Interaktive API-Dokumentation
- **Testen**: Direkt in der Browser-Oberfläche

### ReDoc
- **URL**: http://localhost:8000/redoc
- **Features**: Lesbare API-Dokumentation

## 📊 Datenbank-Inspektion

### SQLite-Datenbank anzeigen
```bash
# SQLite-Browser öffnen (falls installiert)
sqlitebrowser buildwise.db

# Oder über Kommandozeile
sqlite3 buildwise.db

# Tabellen anzeigen
.tables

# Audit-Logs anzeigen
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;

# Benutzer mit DSGVO-Feldern anzeigen
SELECT id, email, status, data_processing_consent, 
       marketing_consent, privacy_policy_accepted, terms_accepted
FROM users;
```

## 🛡️ Sicherheitsfeatures testen

### 1. Passwort-Stärke-Validierung
```bash
# Schwaches Passwort (sollte abgelehnt werden)
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "weak@buildwise.de",
    "password": "123",
    "first_name": "Weak",
    "last_name": "User",
    "user_type": "private",
    "data_processing_consent": true,
    "privacy_policy_accepted": true,
    "terms_accepted": true
  }'
```

### 2. Account-Sperrung testen
```bash
# 5 falsche Login-Versuche
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin@buildwise.de&password=wrongpassword"
done
```

### 3. Audit-Logging prüfen
```bash
# Audit-Logs nach Login-Versuchen anzeigen
sqlite3 buildwise.db "SELECT action, description, created_at FROM audit_logs WHERE action IN ('user_login', 'failed_login', 'account_locked') ORDER BY created_at DESC LIMIT 5;"
```

## 🔧 Troubleshooting

### Häufige Probleme

#### 1. Backend startet nicht
```bash
# Prüfen Sie die .env-Datei
cat .env

# Prüfen Sie die Datenbankverbindung
python -c "from app.core.database import engine; print('Datenbank OK')"
```

#### 2. Frontend kann Backend nicht erreichen
```bash
# CORS-Einstellungen prüfen
# In app/main.py sind bereits CORS-Einstellungen für localhost:5173

# Backend-URL im Frontend prüfen
# In Frontend/Frontend/src/api/api.ts
```

#### 3. DSGVO-Migration fehlgeschlagen
```bash
# Migration erneut ausführen
python migrate_to_gdpr.py

# Datenbank zurücksetzen (Vorsicht!)
rm buildwise.db
python create_tables.py
python migrate_to_gdpr.py
```

#### 4. Tests schlagen fehl
```bash
# Backend läuft?
curl http://localhost:8000/health

# Datenbank ist bereit?
python -c "import sqlite3; conn = sqlite3.connect('buildwise.db'); print('DB OK')"

# Alle Abhängigkeiten installiert?
pip install -r requirements.txt
```

## 📈 Performance-Tests

### Load Testing
```bash
# Mit Apache Bench (falls installiert)
ab -n 100 -c 10 http://localhost:8000/health

# Mit Python requests
python -c "
import requests
import time
start = time.time()
for i in range(100):
    requests.get('http://localhost:8000/health')
print(f'100 Requests in {time.time() - start:.2f} Sekunden')
"
```

### Memory Usage
```bash
# Python Memory Profiler
pip install memory-profiler

python -m memory_profiler test_gdpr_features.py
```

## 🔒 Sicherheitsaudit

### 1. Dependency Check
```bash
# Sicherheitslücken in Abhängigkeiten prüfen
pip install safety
safety check
```

### 2. Code-Qualität
```bash
# Linting
pip install flake8
flake8 app/

# Type Checking
pip install mypy
mypy app/
```

### 3. Test Coverage
```bash
# Test Coverage prüfen
pip install pytest-cov
pytest --cov=app tests/
```

## 📝 Test-Protokoll

### Beispiel-Test-Session
```bash
# 1. System starten
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
cd Frontend/Frontend && npm run dev &

# 2. Vollständige Tests ausführen
cd /c/Users/user/Documents/04_Repo/BuildWise
python test_gdpr_features.py

# 3. Ergebnisse dokumentieren
echo "Test-Ergebnisse: $(date)" >> test_results.log
python test_gdpr_features.py >> test_results.log 2>&1
```

### Erwartete Ergebnisse
- ✅ Health Check: 200 OK
- ✅ Benutzerregistrierung: 201 Created
- ✅ Login: 200 OK mit JWT-Token
- ✅ DSGVO-Features: Alle Endpunkte funktionieren
- ✅ Passwort-Validierung: Schwache Passwörter werden abgelehnt
- ✅ Audit-Logging: Alle Aktionen werden protokolliert

## 🎯 Nächste Schritte

### Für Entwickler
1. **Unit Tests erweitern**: Mehr spezifische Tests für DSGVO-Features
2. **Integration Tests**: End-to-End-Tests für komplette Workflows
3. **Performance Tests**: Load-Testing für Produktionsumgebung

### Für Administratoren
1. **Monitoring einrichten**: Log-Aggregation und Alerting
2. **Backup-Strategie**: Regelmäßige Datenbank-Backups
3. **Sicherheits-Updates**: Regelmäßige Updates der Abhängigkeiten

### Für Compliance
1. **Audit-Trail prüfen**: Regelmäßige Überprüfung der Audit-Logs
2. **DSGVO-Assessment**: Jährliche DSGVO-Compliance-Prüfung
3. **Dokumentation aktualisieren**: DSGVO-Dokumentation aktuell halten

---

**Letzte Aktualisierung**: 2024-01-01  
**Version**: 1.0  
**Verantwortlich**: BuildWise Development Team 