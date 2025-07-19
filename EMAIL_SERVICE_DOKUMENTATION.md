# E-Mail-Service Dokumentation

## Übersicht

Der E-Mail-Service für BuildWise bietet vollständige E-Mail-Funktionalität für:
- E-Mail-Verifizierung bei Registrierung
- Passwort-Reset
- Willkommens-E-Mails
- Kontolöschungs-Bestätigungen

## Konfiguration

### Umgebungsvariablen

Fügen Sie folgende Variablen zu Ihrer `.env` Datei hinzu:

```env
# E-Mail-Konfiguration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@buildwise.de
FROM_NAME=BuildWise

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Gmail-Konfiguration

Für Gmail müssen Sie:
1. 2-Faktor-Authentifizierung aktivieren
2. App-Passwort generieren
3. SMTP_USERNAME = Ihre Gmail-Adresse
4. SMTP_PASSWORD = App-Passwort (nicht Ihr normales Passwort)

## Funktionen

### 1. E-Mail-Verifizierung

**Zweck:** Verifiziert neue Benutzerkonten

**Verwendung:**
```python
from app.services.email_service import email_service

success = email_service.send_verification_email(
    to_email="user@example.com",
    verification_token="token-123",
    user_name="Max Mustermann"
)
```

**E-Mail-Inhalt:**
- Professionelles HTML-Design
- Verifizierungs-Button
- Fallback-URL
- 24-Stunden-Gültigkeit

### 2. Passwort-Reset

**Zweck:** Ermöglicht sichere Passwort-Zurücksetzung

**Verwendung:**
```python
success = email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_token="reset-token-123",
    user_name="Max Mustermann"
)
```

**E-Mail-Inhalt:**
- Sicherheitshinweise
- 1-Stunden-Gültigkeit
- Klare Anweisungen

### 3. Willkommens-E-Mail

**Zweck:** Begrüßt neue Benutzer nach Verifizierung

**Verwendung:**
```python
success = email_service.send_welcome_email(
    to_email="user@example.com",
    user_name="Max Mustermann",
    user_type="Bauträger"
)
```

### 4. Kontolöschungs-E-Mail

**Zweck:** Bestätigt DSGVO-konforme Kontolöschung

**Verwendung:**
```python
success = email_service.send_account_deletion_email(
    to_email="user@example.com",
    user_name="Max Mustermann"
)
```

## API-Endpunkte

### Passwort-Reset anfordern
```http
POST /auth/password-reset
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### Passwort mit Token zurücksetzen
```http
POST /auth/password-reset/{token}
Content-Type: application/json

{
  "new_password": "NeuesPasswort123!"
}
```

## Sicherheitsfeatures

### Token-Sicherheit
- Verifizierungs-Token: 24 Stunden gültig
- Reset-Token: 1 Stunde gültig
- Sichere Token-Generierung mit `secrets.token_urlsafe(32)`

### DSGVO-Konformität
- Klare Einwilligungshinweise
- Opt-out-Möglichkeiten
- Datenlöschungs-Bestätigungen

### Audit-Logging
- Alle E-Mail-Aktivitäten werden protokolliert
- IP-Adressen werden anonymisiert
- Risikobewertung für Sicherheitsereignisse

## Fehlerbehandlung

### SMTP-Fehler
```python
try:
    success = email_service.send_verification_email(...)
    if not success:
        print("E-Mail konnte nicht gesendet werden")
except Exception as e:
    print(f"E-Mail-Service-Fehler: {e}")
```

### Häufige Probleme

1. **Gmail-App-Passwort erforderlich**
   - Aktivieren Sie 2FA
   - Generieren Sie App-Passwort
   - Verwenden Sie App-Passwort, nicht normales Passwort

2. **SMTP-Port blockiert**
   - Verwenden Sie Port 587 (TLS) oder 465 (SSL)
   - Prüfen Sie Firewall-Einstellungen

3. **Rate-Limiting**
   - Gmail: 500 E-Mails/Tag
   - Implementieren Sie Delays bei Massenversand

## Testing

### Test-Script ausführen
```bash
python test_email_service.py
```

### Manueller Test
```python
from app.services.email_service import email_service

# Test-E-Mail senden
success = email_service.send_verification_email(
    "test@example.com",
    "test-token",
    "Test User"
)
print(f"E-Mail gesendet: {success}")
```

## Deployment

### Produktionsumgebung
1. Konfigurieren Sie einen dedizierten E-Mail-Service (SendGrid, Mailgun, etc.)
2. Setzen Sie entsprechende Umgebungsvariablen
3. Testen Sie E-Mail-Delivery
4. Überwachen Sie Bounce-Rates

### Monitoring
- E-Mail-Delivery-Status
- Bounce-Rate
- Spam-Score
- Benutzer-Engagement

## Troubleshooting

### E-Mail wird nicht empfangen
1. Prüfen Sie Spam-Ordner
2. Verifizieren Sie SMTP-Konfiguration
3. Testen Sie mit einfacher E-Mail-Adresse

### SMTP-Verbindungsfehler
1. Prüfen Sie Firewall-Einstellungen
2. Verifizieren Sie SMTP-Credentials
3. Testen Sie mit anderen SMTP-Servern

### Token-Fehler
1. Prüfen Sie Token-Gültigkeit
2. Verifizieren Sie Datenbank-Verbindung
3. Überprüfen Sie Token-Format 