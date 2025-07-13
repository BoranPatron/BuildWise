# 🚀 BuildWise Deployment auf Render.com

Diese Anleitung zeigt dir, wie du BuildWise auf Render.com in der kostenlosen Version deployst.

## 📋 Voraussetzungen

1. **GitHub Account** mit deinem BuildWise Repository
2. **Render.com Account** (kostenlos)
3. **Dein Code muss auf GitHub sein**

## 🔧 Schritt 1: GitHub Repository vorbereiten

### Falls noch nicht auf GitHub:
```bash
# In deinem BuildWise-Ordner
git init
git add .
git commit -m "Initial commit für Render.com Deployment"
git branch -M main
git remote add origin https://github.com/DEIN_USERNAME/buildwise-app.git
git push -u origin main
```

### Falls bereits auf GitHub:
```bash
git add .
git commit -m "Render.com Deployment vorbereiten"
git push
```

## 🌐 Schritt 2: Backend auf Render.com deployen

1. **Gehe zu [dashboard.render.com](https://dashboard.render.com)**
2. **Klicke auf "New +" → "Web Service"**
3. **Verbinde dein GitHub Repository**
4. **Konfiguriere das Backend:**

### Backend-Konfiguration:
- **Name**: `buildwise-backend`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Environment Variables für Backend:
```
DEBUG=false
ENVIRONMENT=production
JWT_SECRET_KEY=dein_super_secret_key_hier
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DB_HOST=localhost
DB_PORT=5432
DB_NAME=buildwise
DB_USER=postgres
DB_PASSWORD=password
```

5. **Klicke "Create Web Service"**
6. **Warte auf das Deployment** (kann 5-10 Minuten dauern)
7. **Notiere die Backend-URL** (z.B. `https://buildwise-backend-abc123.onrender.com`)

## 🎨 Schritt 3: Frontend auf Render.com deployen

1. **Gehe zurück zu [dashboard.render.com](https://dashboard.render.com)**
2. **Klicke auf "New +" → "Static Site"**
3. **Verbinde das gleiche GitHub Repository**
4. **Konfiguriere das Frontend:**

### Frontend-Konfiguration:
- **Name**: `buildwise-frontend`
- **Build Command**: `cd Frontend/Frontend && npm install && npm run build`
- **Publish Directory**: `Frontend/Frontend/dist`

### Environment Variables für Frontend:
```
VITE_API_BASE_URL=https://dein-backend-name.onrender.com/api/v1
```

**Wichtig**: Ersetze `dein-backend-name` mit deiner tatsächlichen Backend-URL!

5. **Klicke "Create Static Site"**
6. **Warte auf das Deployment**

## 🔗 Schritt 4: Verbindung testen

1. **Öffne deine Frontend-URL**
2. **Versuche dich einzuloggen**
3. **Prüfe, ob die API-Calls funktionieren**

## 🛠️ Troubleshooting

### Backend-Probleme:
- **ModuleNotFoundError**: Prüfe `requirements.txt`
- **Import-Fehler**: Prüfe die Imports in `app/main.py`
- **Datenbank-Fehler**: Prüfe die Environment Variables

### Frontend-Probleme:
- **API-Verbindung**: Prüfe `VITE_API_BASE_URL`
- **Build-Fehler**: Prüfe `package.json` und Dependencies
- **CORS-Fehler**: Prüfe die CORS-Konfiguration im Backend

## 📝 Wichtige Hinweise

1. **Kostenlose Version**: Render.com spinnt kostenlose Services nach Inaktivität herunter
2. **Erste Anfrage**: Kann 30-60 Sekunden dauern
3. **Datenbank**: Verwende SQLite für kostenlose Version
4. **Datei-Uploads**: Werden bei kostenloser Version nicht gespeichert

## 🔄 Updates

Für Updates:
```bash
git add .
git commit -m "Update für Render.com"
git push
```

Render.com deployt automatisch bei jedem Push!

## 📞 Support

Bei Problemen:
1. **Prüfe die Logs** in Render.com Dashboard
2. **Teste lokal** zuerst
3. **Prüfe Environment Variables**
4. **Kontaktiere Support** bei Render.com

---

**Viel Erfolg beim Deployment! 🚀** 