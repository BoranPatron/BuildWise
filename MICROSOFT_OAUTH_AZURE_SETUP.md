# Microsoft OAuth Azure AD Setup

## 🔧 Problem: "Benutzerinformationen konnten nicht abgerufen werden"

Das Problem liegt daran, dass die Microsoft Graph API-Berechtigungen nicht korrekt konfiguriert sind.

## 📋 Schritt-für-Schritt Azure AD Konfiguration

### 1. Azure Portal öffnen
- Gehen Sie zu: https://portal.azure.com/
- Melden Sie sich mit Ihrem Microsoft-Konto an

### 2. App Registration finden
- Klicken Sie auf "App registrations"
- Suchen Sie nach "BuildWise" oder Ihrer App-ID: `c5247a29-0cb4-4cdf-9f4c-a091a3a42383`
- Klicken Sie auf die App

### 3. API Permissions konfigurieren
- Im linken Menü: "API permissions"
- Klicken Sie auf "Add a permission"
- Wählen Sie "Microsoft Graph"
- Wählen Sie "Delegated permissions"
- Suchen Sie und aktivieren Sie:
  - ✅ `User.Read` (Standard)
  - ✅ `email`
  - ✅ `openid`
  - ✅ `profile`
- Klicken Sie auf "Add permissions"

### 4. Admin Consent erteilen
- Klicken Sie auf "Grant admin consent for [Ihr Tenant]"
- Bestätigen Sie mit "Yes"

### 5. Redirect URIs prüfen
- Im linken Menü: "Authentication"
- Unter "Platform configurations": "Add a platform"
- Wählen Sie "Single-page application (SPA)"
- Fügen Sie hinzu: `http://localhost:5173/auth/microsoft/callback`
- Speichern Sie

### 6. Client Secret prüfen
- Im linken Menü: "Certificates & secrets"
- Unter "Client secrets" sollte Ihr Secret vorhanden sein
- Falls nicht: "New client secret" erstellen

## 🔍 Debugging

### Backend-Logs prüfen
```bash
# Backend starten und Logs beobachten
python start_server.py
```

### Test-Skript ausführen
```bash
python debug_microsoft_oauth.py
```

### Erwartete Logs
```
🔍 Microsoft OAuth Debug:
  - Client ID: c5247a29-0cb4-4cdf-9f4c-a091a3a42383
  - Access Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIs...
  - Response status: 200
  - User info erfolgreich abgerufen
```

## ⚠️ Häufige Probleme

### 1. Fehlende API Permissions
- **Symptom:** `401 Unauthorized` bei Graph API
- **Lösung:** `User.Read` Permission hinzufügen

### 2. Falsche Redirect URI
- **Symptom:** `redirect_uri_mismatch`
- **Lösung:** URI in Azure Portal prüfen

### 3. Abgelaufener Client Secret
- **Symptom:** `invalid_client`
- **Lösung:** Neuen Client Secret erstellen

### 4. Fehlender Admin Consent
- **Symptom:** `insufficient_privileges`
- **Lösung:** Admin Consent erteilen

## 🚀 Nächste Schritte

1. **Azure AD konfigurieren** (siehe oben)
2. **Backend neu starten**
3. **Frontend neu laden**
4. **Microsoft OAuth testen**

## 📞 Support

Bei Problemen:
1. Backend-Logs prüfen
2. Azure Portal-Konfiguration überprüfen
3. Test-Skript ausführen
4. Fehlermeldungen analysieren 