# Render.com Umgebungsvariablen-Konfiguration

## 🔧 **Erforderliche Umgebungsvariablen in Render.com**

Gehe zu deinem Backend-Service in Render.com und setze folgende Umgebungsvariablen:

### **Datenbank-Konfiguration**
```
DATABASE_URL=postgres://username:password@host:port/database
```
*Diese wird automatisch von Render.com bereitgestellt*

### **JWT-Konfiguration**
```
JWT_SECRET_KEY=dein_super_langer_und_zufaelliger_secret_key_hier_mindestens_32_zeichen
```
*Generiere einen sicheren Secret Key*

### **Anwendungseinstellungen**
```
ENVIRONMENT=production
DEBUG=False
PORT=8000
HOST=0.0.0.0
```

### **CORS-Konfiguration**
```
ALLOWED_ORIGINS=https://buildwise-frontend.onrender.com,http://localhost:3000,http://localhost:5173
ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
ALLOWED_HEADERS=Content-Type,Authorization,X-Requested-With
ALLOW_CREDENTIALS=True
```

## 🚀 **Schritte zur Konfiguration**

1. **Gehe zu Render.com Dashboard**
   - Öffne https://dashboard.render.com
   - Wähle deinen Backend-Service aus

2. **Umgebungsvariablen setzen**
   - Klicke auf "Environment" Tab
   - Füge die oben genannten Variablen hinzu

3. **Deployment auslösen**
   - Nach dem Setzen der Variablen wird automatisch ein neues Deployment ausgelöst

4. **Logs überprüfen**
   - Überwache die Logs während des Deployments
   - Suche nach Fehlermeldungen

## 🔍 **Troubleshooting**

### **Häufige Probleme:**

1. **DATABASE_URL nicht gesetzt**
   - Render.com sollte diese automatisch bereitstellen
   - Prüfe, ob die PostgreSQL-Datenbank erstellt wurde

2. **JWT_SECRET_KEY fehlt**
   - Setze einen sicheren Secret Key
   - Mindestens 32 Zeichen lang

3. **CORS-Fehler**
   - Stelle sicher, dass ALLOWED_ORIGINS die Frontend-URL enthält
   - Füge auch localhost für Entwicklung hinzu

4. **Datenbankverbindung fehlgeschlagen**
   - Prüfe, ob die PostgreSQL-Datenbank läuft
   - Überprüfe die DATABASE_URL

## 🧪 **Test-Skript ausführen**

Nach dem Deployment kannst du das Test-Skript ausführen:

```bash
python test_render_config.py
```

## 📋 **Checkliste**

- [ ] DATABASE_URL gesetzt
- [ ] JWT_SECRET_KEY gesetzt (mindestens 32 Zeichen)
- [ ] ENVIRONMENT=production
- [ ] DEBUG=False
- [ ] ALLOWED_ORIGINS korrekt konfiguriert
- [ ] Backend erfolgreich deployed
- [ ] Test-Skript erfolgreich ausgeführt
- [ ] API-Endpunkte erreichbar

## 🔗 **Nützliche Links**

- [Render.com Key-Value Dokumentation](https://render.com/docs/key-value)
- [Render.com Troubleshooting](https://render.com/docs/troubleshooting-deploys)
- [PostgreSQL auf Render.com](https://render.com/docs/postgres-databases) 