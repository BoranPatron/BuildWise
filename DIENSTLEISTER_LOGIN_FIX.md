# Dienstleister-Login Problem - Behebung

## Problem
Der Dienstleister-Test-Login auf der Login-Seite funktioniert nicht mehr.

## Ursache
Das Frontend verwendete die E-Mail-Adresse `dienstleister@buildwise.de`, aber die Backend-Skripte verwenden `test-dienstleister@buildwise.de`.

## Lösung

### 1. Frontend angepasst ✅
- Die E-Mail-Adresse im Frontend wurde von `dienstleister@buildwise.de` auf `test-dienstleister@buildwise.de` geändert
- Fehlermeldungen wurden verbessert

### 2. Dienstleister-User erstellen
Führe das folgende Skript aus, um den korrekten Dienstleister-User zu erstellen:

```bash
cd BuildWise
python fix_dienstleister_login.py
```

### 3. Backend starten
Stelle sicher, dass das Backend läuft:

```bash
cd BuildWise
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend starten
Stelle sicher, dass das Frontend läuft:

```bash
cd Frontend/Frontend
npm run dev
```

## Anmeldedaten
- **E-Mail**: `test-dienstleister@buildwise.de`
- **Passwort**: `Dienstleister123!`
- **User Role**: `DIENSTLEISTER`

## Test
1. Gehe zur Login-Seite
2. Klicke auf "Dienstleister-Test (admin)"
3. Der Login sollte erfolgreich sein und zur Service-Provider-Seite weiterleiten

## Debugging
Falls der Login immer noch nicht funktioniert:

1. **Prüfe Backend-Logs**: Schauen Sie in die Backend-Konsole für Fehlermeldungen
2. **Prüfe Browser-Konsole**: Öffnen Sie die Entwicklertools (F12) und schauen Sie in die Konsole
3. **Prüfe Netzwerk-Tab**: Schauen Sie sich die API-Aufrufe im Netzwerk-Tab an

## Alternative Skripte
- `check_dienstleister_login.py` - Überprüft beide E-Mail-Adressen
- `create_dienstleister_user.py` - Erstellt User mit `dienstleister@buildwise.de`
- `fix_dienstleister_login.py` - Erstellt User mit `test-dienstleister@buildwise.de` (empfohlen) 