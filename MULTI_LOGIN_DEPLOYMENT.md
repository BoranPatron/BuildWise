# Multi-Login-System Deployment-Anleitung

## Übersicht

Diese Anleitung beschreibt die vollständige Implementierung eines Multi-Login-Systems mit DSGVO-Compliance für BuildWise. Das System unterstützt:

- E-Mail/Passwort-Authentifizierung
- Google OAuth 2.0
- Microsoft Azure AD OAuth 2.0
- Multi-Factor Authentication (MFA)
- DSGVO-Compliance (Datenportabilität, Löschung, Einwilligungen)

## 1. Voraussetzungen

### 1.1 Technische Anforderungen

- Python 3.9+
- PostgreSQL 13+
- Node.js 18+ (für Frontend)
- Redis (optional, für Caching)

### 1.2 Externe Services

#### Google OAuth Setup
1. Google Cloud Console öffnen: https://console.cloud.google.com/
2. Neues Projekt erstellen oder bestehendes auswählen
3. OAuth 2.0 Client ID erstellen:
   - Anwendungstyp: Web-Anwendung
   - Autorisierte Weiterleitungs-URIs:
     - `http://localhost:3000/auth/google/callback` (Development)
     - `https://buildwise.de/auth/google/callback` (Production)
4. Client ID und Client Secret notieren

#### Microsoft Azure AD Setup
1. Azure Portal öffnen: https://portal.azure.com/
2. Azure Active Directory → App registrations
3. Neue Registrierung erstellen:
   - Name: BuildWise
   - Redirect URI: Web
   - URIs: `http://localhost:3000/auth/microsoft/callback` (Development)
4. Client ID, Tenant ID und Client Secret notieren

## 2. Umgebungsvariablen

### 2.1 Backend (.env)

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=buildwise
DB_USER=buildwise_user
DB_PASSWORD=secure_password

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_REDIRECT_URI=http://localhost:3000/auth/microsoft/callback
MICROSOFT_TENANT_ID=your-tenant-id

# Security Settings
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_SPECIAL_CHARS=true
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
SESSION_TIMEOUT_MINUTES=60

# DSGVO Settings
DATA_RETENTION_DAYS=2555
CONSENT_EXPIRY_DAYS=365
DATA_EXPORT_TOKEN_EXPIRY_HOURS=24

# Email Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
FROM_EMAIL=noreply@buildwise.de

# Frontend URLs
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=["http://localhost:3000","https://buildwise.de"]

# Environment
ENVIRONMENT=development
DEBUG=false
```

### 2.2 Frontend (.env)

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_MICROSOFT_CLIENT_ID=your-microsoft-client-id
VITE_APP_NAME=BuildWise
```

## 3. Datenbank-Migration

### 3.1 Neue Migration erstellen

```bash
# Im BuildWise-Verzeichnis
alembic revision --autogenerate -m "Add multi-login support"
alembic upgrade head
```

### 3.2 Manuelle SQL-Updates (falls nötig)

```sql
-- Social-Login Felder hinzufügen
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(20) DEFAULT 'email';
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS microsoft_sub VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS apple_sub VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS social_profile_data JSONB;

-- MFA-Felder hinzufügen
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_backup_codes JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_last_used TIMESTAMP;

-- DSGVO-Erweiterungen
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_fields JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_history JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS data_export_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS data_export_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS data_export_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS data_export_requested_at TIMESTAMP;

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub);
CREATE INDEX IF NOT EXISTS idx_users_microsoft_sub ON users(microsoft_sub);
CREATE INDEX IF NOT EXISTS idx_users_auth_provider ON users(auth_provider);
```

## 4. Backend-Deployment

### 4.1 Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4.2 Datenbank initialisieren

```bash
# Migration ausführen
alembic upgrade head

# Testdaten erstellen (optional)
python create_test_data.py
```

### 4.3 Backend starten

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 5. Frontend-Deployment

### 5.1 Dependencies installieren

```bash
cd Frontend/Frontend
npm install
```

### 5.2 Frontend starten

```bash
# Development
npm run dev

# Production Build
npm run build
npm run preview
```

## 6. Docker-Deployment

### 6.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=buildwise
      - DB_USER=buildwise_user
      - DB_PASSWORD=secure_password
    depends_on:
      - db
    volumes:
      - ./storage:/app/storage

  frontend:
    build: ./Frontend/Frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=buildwise
      - POSTGRES_USER=buildwise_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### 6.2 Docker starten

```bash
docker-compose up -d
```

## 7. SSL/HTTPS Setup

### 7.1 Let's Encrypt (Production)

```bash
# Certbot installieren
sudo apt install certbot

# Zertifikat erstellen
sudo certbot certonly --standalone -d buildwise.de -d www.buildwise.de

# Nginx-Konfiguration
sudo nano /etc/nginx/sites-available/buildwise
```

### 7.2 Nginx-Konfiguration

```nginx
server {
    listen 80;
    server_name buildwise.de www.buildwise.de;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name buildwise.de www.buildwise.de;

    ssl_certificate /etc/letsencrypt/live/buildwise.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/buildwise.de/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 8. Monitoring und Logging

### 8.1 Logging-Konfiguration

```python
# app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('logs/buildwise.log', maxBytes=10485760, backupCount=5),
            logging.StreamHandler()
        ]
    )
```

### 8.2 Health Checks

```bash
# Backend Health Check
curl http://localhost:8000/health

# Frontend Health Check
curl http://localhost:3000/
```

## 9. Security Checklist

### 9.1 Pre-Deployment

- [ ] Alle Secrets in Umgebungsvariablen
- [ ] HTTPS/SSL konfiguriert
- [ ] Firewall-Regeln gesetzt
- [ ] Datenbank-Backup-Strategie
- [ ] Monitoring eingerichtet

### 9.2 Post-Deployment

- [ ] OAuth-Clients getestet
- [ ] MFA-Funktionalität geprüft
- [ ] DSGVO-Funktionen validiert
- [ ] Security-Scan durchgeführt
- [ ] Performance-Tests ausgeführt

## 10. Troubleshooting

### 10.1 Häufige Probleme

#### OAuth-Fehler
```bash
# Logs prüfen
tail -f logs/buildwise.log | grep oauth

# OAuth-URLs testen
curl "http://localhost:8000/auth/oauth/google/url"
```

#### Datenbank-Verbindung
```bash
# PostgreSQL-Status
sudo systemctl status postgresql

# Verbindung testen
psql -h localhost -U buildwise_user -d buildwise
```

#### Frontend-Backend-Kommunikation
```bash
# CORS-Probleme prüfen
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost:8000/auth/login
```

### 10.2 Debug-Modus

```bash
# Backend mit Debug
DEBUG=true uvicorn app.main:app --reload

# Frontend mit Debug
npm run dev -- --debug
```

## 11. Wartung und Updates

### 11.1 Regelmäßige Tasks

```bash
# Logs rotieren
logrotate /etc/logrotate.d/buildwise

# Datenbank-Backup
pg_dump buildwise > backup_$(date +%Y%m%d).sql

# DSGVO-Datenbereinigung
python -c "from app.services.gdpr_service import GDPRService; GDPRService.cleanup_expired_data()"
```

### 11.2 Updates

```bash
# Backend-Update
git pull origin main
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart buildwise-backend

# Frontend-Update
cd Frontend/Frontend
git pull origin main
npm install
npm run build
sudo systemctl restart buildwise-frontend
```

## 12. Support und Dokumentation

### 12.1 API-Dokumentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 12.2 Monitoring

- Application Metrics: `http://localhost:8000/metrics`
- Health Status: `http://localhost:8000/health`

### 12.3 Kontakt

- Technischer Support: tech@buildwise.de
- Datenschutz: datenschutz@buildwise.de
- Sicherheit: security@buildwise.de 