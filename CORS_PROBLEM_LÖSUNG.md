# CORS-Problem Lösung für Geo-Karten

## Problem
Die Gewerke werden nicht auf der Karte angezeigt wegen eines CORS-Problems:
```
Quellübergreifende (Cross-Origin) Anfrage blockiert: Die Gleiche-Quelle-Regel verbietet das Lesen der externen Ressource auf http://localhost:8000/api/v1/geo/search-trades. (Grund: CORS-Anfrage schlug fehl). Statuscode: (null).
```

## Status
✅ **Backend läuft**: Das Backend ist auf Port 8000 verfügbar  
❌ **CORS-Problem**: Frontend kann nicht mit Backend kommunizieren

## Lösung

### 1. Backend-Neustart (bereits durchgeführt)
Das Backend wurde neu gestartet und läuft jetzt korrekt.

### 2. Testen Sie die Verbindung

**Option A: Verwenden Sie das Test-Skript**
1. Öffnen Sie die Browser-Entwicklertools (F12)
2. Kopieren Sie den Inhalt von `Frontend/Frontend/debug_cors_fix.js`
3. Führen Sie ihn in der Konsole aus
4. Überprüfen Sie die Debug-Ausgaben

**Option B: Manueller Test**
1. Öffnen Sie `http://localhost:8000/docs` im Browser
2. Prüfen Sie, ob die API-Dokumentation angezeigt wird
3. Testen Sie die Authentifizierung

### 3. Frontend-Neustart
Falls das Problem weiterhin besteht:

1. **Stoppen Sie das Frontend** (falls es läuft)
2. **Starten Sie das Frontend neu**:
   ```bash
   cd Frontend/Frontend
   npm run dev
   ```
3. **Öffnen Sie die Anwendung** im Browser
4. **Melden Sie sich an** als Dienstleister
5. **Testen Sie die Kartenansicht**

### 4. Browser-Cache leeren
Falls das Problem weiterhin besteht:

1. **Öffnen Sie die Browser-Entwicklertools** (F12)
2. **Rechtsklick auf den Reload-Button**
3. **Wählen Sie "Leerer Cache und hartes Neuladen"**
4. **Testen Sie erneut**

### 5. Alternative URL testen
Falls das Problem weiterhin besteht, testen Sie verschiedene URLs:

- `http://localhost:8000/api/v1/geo/search-trades`
- `http://127.0.0.1:8000/api/v1/geo/search-trades`
- `https://localhost:8000/api/v1/geo/search-trades`

## Debug-Schritte

### Schritt 1: Backend-Verfügbarkeit prüfen
```javascript
// In der Browser-Konsole ausführen
fetch('http://localhost:8000/docs')
  .then(response => console.log('Backend Status:', response.status))
  .catch(error => console.error('Backend-Fehler:', error));
```

### Schritt 2: API mit Authentifizierung testen
```javascript
// In der Browser-Konsole ausführen (nach Anmeldung)
const token = localStorage.getItem('token');
fetch('http://localhost:8000/api/v1/geo/search-trades', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    latitude: 52.5200,
    longitude: 13.4050,
    radius_km: 50,
    limit: 10
  })
})
.then(response => response.json())
.then(data => console.log('API-Ergebnisse:', data))
.catch(error => console.error('API-Fehler:', error));
```

### Schritt 3: Frontend-Konfiguration prüfen
```javascript
// In der Browser-Konsole ausführen
console.log('Aktuelle URL:', window.location.href);
console.log('Hostname:', window.location.hostname);
console.log('Port:', window.location.port);
console.log('Protocol:', window.location.protocol);
```

## Erwartete Ergebnisse

### Erfolg
- ✅ Backend antwortet mit Status 200
- ✅ API liefert Gewerke mit Koordinaten
- ✅ Gewerke erscheinen als Marker auf der Karte

### Fehler
- ❌ Backend nicht erreichbar → Backend neu starten
- ❌ CORS-Fehler → Browser-Cache leeren
- ❌ Authentifizierungsfehler → Anmelden und Token prüfen
- ❌ Keine Gewerke → Datenbank-Behebung prüfen

## Nächste Schritte

1. **Führen Sie das Test-Skript aus** (`debug_cors_fix.js`)
2. **Überprüfen Sie die Debug-Ausgaben**
3. **Folgen Sie den Anweisungen** basierend auf den Ergebnissen
4. **Testen Sie die Kartenansicht** erneut

## Support

Falls das Problem weiterhin besteht:
1. Überprüfen Sie die Browser-Konsole auf Fehler
2. Testen Sie die API-Endpunkte direkt
3. Prüfen Sie die Backend-Logs
4. Verwenden Sie die bereitgestellten Debug-Skripte

---
**Status**: 🔧 IN BEARBEITUNG  
**Datum**: 18. Juli 2025  
**Version**: 1.0 