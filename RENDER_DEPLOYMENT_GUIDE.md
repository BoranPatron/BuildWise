# 🚀 Render.com Deployment Guide für BuildWise

## 📋 Übersicht

Dieser Guide erklärt, wie BuildWise auf Render.com deployed wird, einschließlich der Datenbank-Konfiguration.

## 🗄️ Datenbank-Optionen auf Render.com

### **Option 1: PostgreSQL (Empfohlen)**
- **Persistente Daten** - bleiben auch nach Neustarts erhalten
- **Kostenlos** verfügbar auf Render.com
- **Automatische Backups**
- **Skalierbar**

### **Option 2: SQLite (Nur für Tests)**
- **Temporäre Daten** - gehen bei Neustarts verloren
- **Nicht für Produktion empfohlen**
- **Kostenlos**

## 🔧 Setup-Schritte

### **1. PostgreSQL-Datenbank erstellen**

1. **Gehe zu Render.com Dashboard**
2. **Klicke "New +" → "PostgreSQL"**
3. **Konfiguriere:**
   - **Name:** `buildwise-db`
   - **Database:** `buildwise`
   - **User:** `buildwise_user`
   - **Region:** `Frankfurt (EU Central)`
4. **Klicke "Create Database"**

### **2. Backend-Service erstellen**

1. **Klicke "New +" → "Web Service"**
2. **Verbinde mit GitHub Repository**
3. **Konfiguriere:**
   - **Name:** `buildwise-backend`
   - **Root Directory:** `/` (Backend ist im Root)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### **3. Environment Variables setzen**

**Backend Environment Variables:**
```
DATABASE_URL=postgresql://buildwise_user:password@host:port/buildwise
JWT_SECRET_KEY=your_super_secret_jwt_key_here_make_it_long_and_random
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=False
ENVIRONMENT=production
```

**Frontend Environment Variables:**
```
VITE_API_BASE_URL=https://buildwise-backend.onrender.com/api/v1
```

### **4. Datenbank initialisieren**

Nach dem ersten Deployment:

1. **Gehe zu deinem Backend-Service**
2. **Klicke "Shell"**
3. **Führe aus:**
   ```bash
   python setup_render_database.py
   ```

## 🔄 Automatisches Deployment

### **render.yaml (Automatische Konfiguration)**

```yaml
services:
  # PostgreSQL Database
  - type: pserv
    name: buildwise-db
    env: postgresql
    plan: free
    region: frankfurt

  # Backend Service
  - type: web
    name: buildwise-backend
    env: python
    plan: free
    region: frankfurt
    buildCommand: pip install -r requirements.txt
    startCommand: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: buildwise-db
          property: connectionString
      - key: JWT_SECRET_KEY
        value: your_super_secret_jwt_key_here_make_it_long_and_random
      - key: JWT_ALGORITHM
        value: HS256
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: 30
      - key: DEBUG
        value: false
      - key: ENVIRONMENT
        value: production

  # Frontend Service
  - type: web
    name: buildwise-frontend
    env: static
    plan: free
    region: frankfurt
    buildCommand: cd Frontend/Frontend && npm install && npm run build
    staticPublishPath: Frontend/Frontend/dist
    envVars:
      - key: VITE_API_BASE_URL
        value: https://buildwise-backend.onrender.com/api/v1
```

## 🧪 Test-Daten erstellen

### **Option 1: Über API-Endpunkte**

```bash
# Admin-User erstellen
curl -X POST https://buildwise-backend.onrender.com/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@buildwise.de",
    "password": "admin123",
    "first_name": "Admin",
    "last_name": "User",
    "user_type": "admin"
  }'

# Service Provider erstellen
curl -X POST https://buildwise-backend.onrender.com/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-dienstleister@buildwise.de",
    "password": "test1234",
    "first_name": "Test",
    "last_name": "Dienstleister",
    "user_type": "service_provider"
  }'
```

### **Option 2: Über das Frontend**

1. **Öffne die Frontend-URL**
2. **Logge dich mit den Test-Zugangsdaten ein**
3. **Erstelle Projekte und Daten über die UI**

## 🔍 Troubleshooting

### **Problem: Datenbank-Verbindung fehlgeschlagen**
```bash
# Prüfe DATABASE_URL
echo $DATABASE_URL

# Teste Verbindung
python -c "
import asyncio
from app.core.database import engine
async def test():
    try:
        async with engine.begin() as conn:
            print('✅ Datenbank-Verbindung erfolgreich')
    except Exception as e:
        print(f'❌ Fehler: {e}')
asyncio.run(test())
"
```

### **Problem: Frontend kann Backend nicht erreichen**
1. **Prüfe CORS-Konfiguration im Backend**
2. **Prüfe VITE_API_BASE_URL im Frontend**
3. **Prüfe Backend-URL in der Browser-Konsole**

### **Problem: Kostenpositionen werden nicht angezeigt**
1. **Prüfe ob Quotes akzeptiert wurden**
2. **Führe das Fix-Skript aus:**
   ```bash
   python fix_missing_cost_positions.py
   ```

## 📊 Monitoring

### **Backend-Logs**
- **Render.com Dashboard → Backend-Service → Logs**
- **Prüfe auf Fehler und Warnings**

### **Datenbank-Monitoring**
- **Render.com Dashboard → PostgreSQL → Metrics**
- **Prüfe Verbindungen und Performance**

## 🔒 Sicherheit

### **Environment Variables**
- **Niemals Secrets in Code committen**
- **Verwende Render.com Environment Variables**
- **Regelmäßig Secrets rotieren**

### **CORS-Konfiguration**
```python
# In app/main.py
origins = [
    "https://buildwise-frontend.onrender.com",
    "http://localhost:3000",
    "http://localhost:5173"
]
```

## 🚀 Deployment-Checkliste

- [ ] PostgreSQL-Datenbank erstellt
- [ ] Backend-Service deployed
- [ ] Frontend-Service deployed
- [ ] Environment Variables gesetzt
- [ ] Datenbank initialisiert
- [ ] CORS konfiguriert
- [ ] Test-Daten erstellt
- [ ] Login getestet
- [ ] Kostenpositionen getestet

## 📞 Support

Bei Problemen:
1. **Prüfe Render.com Logs**
2. **Teste lokale Entwicklung**
3. **Prüfe Environment Variables**
4. **Kontaktiere Support mit Logs** 