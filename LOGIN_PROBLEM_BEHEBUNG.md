# Login-Problem Behebung

## Problem
Der Dienstleister-Test-Login schlägt mit 401 Unauthorized Fehler fehl.

## Ursache
Der Dienstleister-User existiert möglicherweise nicht in der Datenbank oder hat falsche Anmeldedaten.

## Lösung

### Schritt 1: Backend starten
```bash
cd BuildWise
python start_backend.py
```

### Schritt 2: Debug-Login ausführen
```bash
cd BuildWise
python debug_login.py
```

Dieses Skript wird:
- Prüfen ob der User existiert
- Den User erstellen falls er nicht existiert
- Das Passwort überprüfen
- Alle Login-Bedingungen testen

### Schritt 3: Frontend testen
1. Gehe zur Login-Seite
2. Klicke auf "Dienstleister-Test (admin)"
3. Der Login sollte jetzt funktionieren

## Alternative: Manuelle User-Erstellung

Falls das Debug-Skript nicht funktioniert, erstelle den User manuell:

```bash
cd BuildWise
python fix_dienstleister_login.py
```

## Anmeldedaten
- **E-Mail**: `test-dienstleister@buildwise.de`
- **Passwort**: `Dienstleister123!`
- **User Role**: `DIENSTLEISTER`

## Debugging

### Backend-Logs prüfen
Schauen Sie in die Backend-Konsole für detaillierte Fehlermeldungen.

### Browser-Konsole prüfen
1. Öffnen Sie die Entwicklertools (F12)
2. Gehen Sie zum "Network"-Tab
3. Versuchen Sie den Login
4. Schauen Sie sich die API-Aufrufe an

### Datenbank prüfen
```bash
cd BuildWise
python check_dienstleister_login.py
```

## Häufige Probleme

### 1. Backend läuft nicht
- Starten Sie das Backend mit `python start_backend.py`
- Prüfen Sie ob Port 8000 frei ist

### 2. User existiert nicht
- Führen Sie `python debug_login.py` aus
- Das Skript erstellt den User automatisch

### 3. Falsche Anmeldedaten
- Verwenden Sie: `test-dienstleister@buildwise.de`
- Passwort: `Dienstleister123!`

### 4. DSGVO-Einwilligungen fehlen
- Das Debug-Skript setzt alle erforderlichen Einwilligungen

## Erfolgreicher Login
Nach erfolgreichem Login sollten Sie:
1. Zur Service-Provider-Seite weitergeleitet werden
2. Die Debug-Informationen im Dashboard sehen
3. Zugang zu den Dienstleister-Funktionen haben 