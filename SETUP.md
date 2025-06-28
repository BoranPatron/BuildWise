# BuildWise Setup-Anleitung

## Backend Setup

### 1. Umgebung einrichten

```bash
cd BuildWise
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Umgebungsvariablen konfigurieren

```bash
# Kopiere die Beispiel-Umgebungsdatei
cp env.example .env

# Bearbeite .env mit deinen Werten:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=buildwise
DB_USER=postgres
DB_PASSWORD=your_password
JWT_SECRET_KEY=your_secret_key_here
```

### 3. Datenbank initialisieren

```bash
# Erstelle Admin-Account
python create_admin.py

# Oder starte das Backend und verwende den Debug-Login
```

### 4. Backend starten

```bash
# Für lokale Entwicklung:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Für Netzwerk-Zugriff:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Backend testen

- Öffne: http://localhost:8000/docs (API-Dokumentation)
- Öffne: http://localhost:8000/health (Health-Check)
- Öffne: http://localhost:8000/ (Root-Endpoint)

## Frontend Setup

### 1. Abhängigkeiten installieren

```bash
cd Frontend/Frontend
npm install
```

### 2. Frontend starten

```bash
npm run dev
```

### 3. Frontend testen

- Öffne: http://localhost:5173
- Verwende den "Backend-Verbindung testen" Button
- Verwende den "Direkt als Admin einloggen" Button

## Debug-Login

### Automatischer Debug-Login

Das Backend hat einen speziellen Debug-Login-Endpoint:
- **URL**: `POST /api/v1/auth/debug-login`
- **Funktion**: Erstellt automatisch einen Admin-Account falls nicht vorhanden
- **Zugangsdaten**: admin@buildwise.de / admin123

### Manueller Admin-Account

```bash
cd BuildWise
python create_admin.py
```

## Netzwerk-Zugriff

### Frontend über Netzwerk erreichbar machen

Das Frontend ist bereits konfiguriert für Netzwerk-Zugriff:
- **Host**: 0.0.0.0 (alle lokalen IPs)
- **Port**: 5173
- **Zugriff**: http://IHRE_IP_ADRESSE:5173

### Backend für Netzwerk-Zugriff konfigurieren

Das Backend muss mit Netzwerk-Host gestartet werden:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### IP-Adresse ermitteln

- **Windows**: `ipconfig` in der Kommandozeile
- **Mac/Linux**: `ifconfig` oder `ip addr` im Terminal
- Suchen Sie nach Ihrer lokalen IP (meist 192.168.x.x oder 10.x.x.x)

## Fehlerbehebung

### Debug-Login funktioniert nicht

1. **Backend läuft nicht**: Starten Sie das Backend mit `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

2. **Datenbank nicht initialisiert**: Führen Sie `python create_admin.py` aus

3. **Port 8000 belegt**: Verwenden Sie einen anderen Port: `--port 8001`

4. **CORS-Fehler**: Das Backend ist bereits für CORS konfiguriert

### Frontend kann Backend nicht erreichen

1. **API-URL prüfen**: Das Frontend verwendet automatisch die richtige IP
2. **Firewall**: Erlauben Sie Port 8000 in der Firewall
3. **Backend-Host**: Stellen Sie sicher, dass das Backend mit `--host 0.0.0.0` läuft

### "Backend nicht erreichbar" Fehler

1. **Backend läuft auf 127.0.0.1**: Das Frontend ist jetzt konfiguriert, um 127.0.0.1 zu verwenden
2. **Health-Check funktioniert nicht**: Der Health-Check verwendet jetzt den korrekten Endpoint `/health`
3. **API-Test**: Verwenden Sie den "API-Verbindung testen" Button für detaillierte Diagnose

### Keiner der Buttons funktioniert

1. **Backend starten**: 
   ```bash
   cd BuildWise
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Backend-Status prüfen**: 
   - Öffnen Sie http://127.0.0.1:8000/health im Browser
   - Sollte `{"status": "healthy", "service": "BuildWise API", "version": "1.0.0"}` anzeigen

3. **Frontend neu laden**: 
   - Drücken Sie F5 oder Ctrl+R im Browser
   - Schauen Sie auf die Backend-Status-Anzeige (grün = online, rot = offline)

4. **Browser-Entwicklertools**: 
   - Drücken Sie F12 → Console
   - Schauen Sie nach Fehlermeldungen
   - Testen Sie die Buttons und schauen Sie in die Console-Logs

5. **CORS-Problem**: 
   - Das Backend ist für CORS konfiguriert
   - Falls es trotzdem nicht funktioniert, starten Sie das Backend neu

### Netzwerk-Zugriff funktioniert nicht

1. **IP-Adresse prüfen**: Verwenden Sie die korrekte lokale IP
2. **Firewall-Einstellungen**: Erlauben Sie Vite und Python in der Firewall
3. **Router-Einstellungen**: Für externe Zugriffe müssen Ports weitergeleitet werden

### "NetworkError when attempting to fetch resource" Fehler

1. **Backend läuft nicht**: 
   ```bash
   cd BuildWise
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Backend-Status prüfen**: 
   - Öffnen Sie http://127.0.0.1:8000/health im Browser
   - Sollte `{"status": "healthy", "service": "BuildWise API", "version": "1.0.0"}` anzeigen

3. **API-Endpoint prüfen**: 
   - Öffnen Sie http://127.0.0.1:8000/api/v1/projects im Browser
   - Sollte `{"detail": "Not authenticated"}` anzeigen (das ist gut - API ist erreichbar)

4. **CORS-Problem**: 
   - Das Backend ist für CORS konfiguriert
   - Falls es trotzdem nicht funktioniert, starten Sie das Backend neu

5. **Firewall-Einstellungen**: 
   - Erlauben Sie Port 8000 in der Windows-Firewall
   - Erlauben Sie Python in der Firewall

6. **Browser-Cache leeren**: 
   - Drücken Sie Ctrl+Shift+R (Hard Refresh)
   - Oder öffnen Sie die Entwicklertools (F12) → Network → "Disable cache"

7. **Alternative Test-Methode**: 
   - Verwenden Sie den "Backend-Verbindung testen" Button zuerst
   - Dieser testet den Health-Check-Endpoint ohne API-Prefix

## API-Endpoints

### Authentifizierung
- `POST /api/v1/auth/login` - Normaler Login
- `POST /api/v1/auth/debug-login` - Debug-Login (erstellt Admin)
- `POST /api/v1/auth/register` - Benutzerregistrierung

### Projekte
- `GET /api/v1/projects` - Alle Projekte
- `POST /api/v1/projects` - Projekt erstellen
- `GET /api/v1/projects/{id}` - Projekt-Details

### Weitere Module
- Tasks: `/api/v1/tasks`
- Documents: `/api/v1/documents`
- Milestones: `/api/v1/milestones`
- Quotes: `/api/v1/quotes`
- Messages: `/api/v1/messages`
- Users: `/api/v1/users`

## Entwicklung

### Backend-Logs aktivieren

```bash
# Detaillierte Logs
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### Frontend-Logs aktivieren

Öffnen Sie die Browser-Entwicklertools (F12) und schauen Sie in die Konsole.

### Datenbank zurücksetzen

```bash
# Datenbank löschen und neu erstellen
rm buildwise.db
python create_admin.py
```

## Sicherheitshinweise

- Diese Konfiguration ist nur für lokale Entwicklung gedacht
- Verwenden Sie in Produktionsumgebungen HTTPS und entsprechende Sicherheitsmaßnahmen
- Beschränken Sie den Netzwerk-Zugriff auf vertrauenswürdige Geräte
- Ändern Sie die Standard-Passwörter in Produktionsumgebungen 