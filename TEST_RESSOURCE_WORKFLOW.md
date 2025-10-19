# Test-Anleitung: Ressource-zu-Angebot Workflow

## ✅ Implementierte Änderungen

### Backend
1. ✅ Benachrichtigung wird bei Allocation-Erstellung gesendet
2. ✅ Resource wird korrekt geladen (nicht mehr lazy)
3. ✅ Logging für Debugging hinzugefügt
4. ✅ Neue Endpoints: `/allocations/my-pending`, `/allocations/{id}/submit-quote`, `/allocations/{id}/reject`

### Frontend
1. ✅ Pending Allocations werden geladen
2. ✅ "Aktion erforderlich" Banner mit Animation
3. ✅ Buttons "Angebot abgeben" und "Ablehnen"
4. ✅ Handler-Funktionen implementiert

## 🧪 Test-Schritte

### 1. Backend starten
```bash
cd BuildWise
python main.py
```

### 2. Frontend starten
```bash
cd Frontend/Frontend
npm run dev
```

### 3. Test-Szenario

#### Als Bauträger:
1. Login als Bauträger
2. Gehe zu einem Projekt → Gewerk
3. Klicke auf "Zugeordnete Ressourcen" → "Ressourcen hinzufügen"
4. Wähle eine Ressource eines Dienstleisters aus
5. Setze Zeitraum und Personenzahl
6. Klicke "Ressource zuordnen"

**Erwartetes Ergebnis:**
- ResourceAllocation wird erstellt mit Status `PRE_SELECTED`
- Benachrichtigung wird an Dienstleister gesendet
- In der Konsole erscheint:
  ```
  ✅ Allocation erstellt: ID=X, Resource=Y, Trade=Z, Status=pre_selected
  🔔 Erstelle Benachrichtigung für Allocation X, Service Provider Y
  ✅ Benachrichtigung erfolgreich erstellt für Service Provider Y
  ```

#### Als Dienstleister:
1. Logout und Login als Dienstleister (dem die Ressource gehört)
2. Gehe zu "Ressourcenverwaltung"

**Erwartetes Ergebnis:**
- ⚠️ **Gelber "Aktion erforderlich" Banner** erscheint oben
- Banner zeigt Anzahl der pendenten Allocations
- Jede Allocation zeigt:
  - Gewerk-Titel
  - Projekt-Name
  - Personenzahl und Zeitraum
  - Status "Wartet auf Angebot"
  - 2 Buttons: "Angebot abgeben" und "Ablehnen"

3. Klicke auf "Ablehnen"
   - Popup erscheint: "Bitte geben Sie einen Ablehnungsgrund ein"
   - Gib Grund ein → OK
   
**Erwartetes Ergebnis:**
- Success-Meldung: "✅ Zuordnung erfolgreich abgelehnt"
- Banner verschwindet
- Ressource Status wird zurückgesetzt auf `available`
- ResourceAllocation Status → `REJECTED`

4. Klicke auf "Angebot abgeben"

**Erwartetes Ergebnis:**
- Alert: "Angebots-Modal wird implementiert"
- In Console: Allocation-Daten werden geloggt

### 4. Debugging

Falls Benachrichtigung nicht erscheint, prüfe:

1. **Backend-Konsole** auf Fehler:
   ```
   ❌ Fehler beim Erstellen der Benachrichtigung: ...
   ```

2. **Browser-Konsole** auf API-Fehler:
   ```javascript
   ❌ Error loading pending allocations: ...
   ```

3. **Datenbank-Check**:
   ```sql
   -- Prüfe ob Allocations erstellt wurden
   SELECT * FROM resource_allocations 
   WHERE allocation_status = 'pre_selected'
   ORDER BY created_at DESC;
   
   -- Prüfe ob Benachrichtigungen erstellt wurden
   SELECT * FROM notifications 
   WHERE type = 'RESOURCE_ALLOCATED'
   ORDER BY created_at DESC;
   ```

4. **API-Test mit curl**:
   ```bash
   # Als Dienstleister einloggen und pending allocations holen
   curl -X GET "http://localhost:8000/api/v1/resources/allocations/my-pending" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## 🐛 Bekannte Probleme & Lösungen

### Problem: Keine Benachrichtigung
**Ursache:** Resource.service_provider_id konnte nicht geladen werden
**Lösung:** ✅ Behoben - Resource wird jetzt explizit geladen

### Problem: Pending Allocations leer
**Ursache:** Status ist nicht `PRE_SELECTED`
**Lösung:** Prüfe beim Erstellen ob `allocation_status` korrekt gesetzt wird

### Problem: Frontend zeigt nichts an
**Ursache:** API-Endpoint wird nicht korrekt aufgerufen
**Lösung:** Prüfe Browser Network Tab → `/allocations/my-pending`

## 📝 Nächste Schritte

1. ✅ Backend: Benachrichtigungen funktionieren
2. ✅ Frontend: Pending Allocations werden angezeigt
3. ✅ Frontend: Ablehnen funktioniert
4. ⏳ **TODO:** Angebots-Modal implementieren (ResourceQuoteModal.tsx)
5. ⏳ **TODO:** Benachrichtigungs-Tab erweitern
6. ⏳ **TODO:** TradeDetailsModal Filter

## 🎯 Erfolgs-Kriterien

- [x] Bauträger kann Ressource zuordnen
- [x] Dienstleister erhält Benachrichtigung (Backend)
- [x] Dienstleister sieht "Aktion erforderlich" Banner
- [x] Dienstleister kann ablehnen
- [ ] Dienstleister kann Angebot abgeben
- [ ] Angebot erscheint beim Bauträger
- [ ] Ressource verschwindet aus "Zugeordnete Ressourcen"

