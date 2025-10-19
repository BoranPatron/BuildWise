# Implementierung: Benachrichtigung als gelesen markieren

## Problem

Wenn der Dienstleister ein Angebot erstellt hat, soll die ursprüngliche Benachrichtigung "Ressource einer Ausschreibung zugeordnet" automatisch als gelesen/inaktiv markiert werden, da die Aktion abgeschlossen ist.

## Lösung

### Backend-Implementierung (`BuildWise/app/api/resources.py`)

Im Endpoint `submit_quote_from_allocation` wurde nach der erfolgreichen Angebots-Erstellung folgender Code hinzugefügt:

```python
# Markiere ursprüngliche "resource_allocated" Benachrichtigung als gelesen
try:
    from ..models.notification import Notification
    notification_query = select(Notification).where(
        Notification.recipient_id == current_user.id,
        Notification.type == 'RESOURCE_ALLOCATED',
        Notification.data.like(f'%"allocation_id": {allocation_id}%')
    )
    notification_result = await db.execute(notification_query)
    resource_notification = notification_result.scalar_one_or_none()
    
    if resource_notification:
        resource_notification.is_acknowledged = True
        resource_notification.acknowledged_at = datetime.now()
        await db.commit()
        print(f"[OK] Ursprüngliche resource_allocated Benachrichtigung als gelesen markiert: ID={resource_notification.id}")
    else:
        print(f"[WARN] Keine resource_allocated Benachrichtigung für Allocation {allocation_id} gefunden")
except Exception as e:
    print(f"[WARN] Fehler beim Markieren der ursprünglichen Benachrichtigung: {e}")
    # Fehler nicht weiterwerfen, da die Hauptfunktion erfolgreich war
```

### Funktionsweise

1. **Query-Parameter:**
   - `recipient_id`: Aktueller Dienstleister (User)
   - `type`: `'RESOURCE_ALLOCATED'` (Enum-Wert aus der DB)
   - `data`: JSON-String mit `"allocation_id": {allocation_id}`

2. **LIKE-Query:**
   - Verwendet `LIKE` statt `contains` für bessere SQLite-Kompatibilität
   - Sucht nach `%"allocation_id": {allocation_id}%` im JSON-String

3. **Update:**
   - `is_acknowledged = True`
   - `acknowledged_at = datetime.now()`
   - `await db.commit()`

### Test-Ergebnis

**Erfolgreicher Test:**
```
[OK] Allocation gefunden: ID=17, Resource=4, Trade=6
[DEBUG] Gefundene Benachrichtigung: <Notification(id=9, type=resource_allocated, recipient_id=125, title='Ressource einer Ausschreibung zugeordnet')>
[OK] Ursprüngliche resource_allocated Benachrichtigung als gelesen markiert: ID=9
[OK] Quote erfolgreich erstellt: {'message': 'Angebot erfolgreich erstellt', 'quote_id': 10, 'allocation_id': 17, 'status': 'offer_submitted'}
```

### Frontend-Verhalten

Nach der Angebots-Abgabe:
1. ✅ Ursprüngliche Benachrichtigung wird als gelesen markiert (`is_acknowledged = True`)
2. ✅ Benachrichtigung verschwindet aus der "Neue Benachrichtigungen" Liste
3. ✅ Benachrichtigung erscheint in der "Gelesene Benachrichtigungen" Liste (falls implementiert)
4. ✅ Dienstleister sieht keine "Aktion erforderlich" Meldung mehr

### Workflow Ende-zu-Ende

1. **Bauträger ordnet Ressource zu** → `resource_allocated` Benachrichtigung erstellt
2. **Dienstleister sieht Benachrichtigung** → "Aktion erforderlich" angezeigt
3. **Dienstleister klickt auf Benachrichtigung** → CostEstimateForm öffnet sich
4. **Dienstleister gibt Angebot ab** → Quote wird erstellt
5. **Backend markiert ursprüngliche Benachrichtigung als gelesen** → `is_acknowledged = True`
6. **Benachrichtigung verschwindet aus "Neue" Liste** → Workflow abgeschlossen

### Fehlerbehandlung

- **Keine Benachrichtigung gefunden:** Warnung wird geloggt, aber Hauptfunktion läuft weiter
- **Fehler beim Update:** Fehler wird geloggt, aber Hauptfunktion läuft weiter
- **Transaktionale Sicherheit:** Update erfolgt nach erfolgreicher Quote-Erstellung

### Geänderte Dateien

**Backend:**
- `BuildWise/app/api/resources.py` - `submit_quote_from_allocation` Endpoint

### Status

✅ **IMPLEMENTIERT UND GETESTET**

Die ursprüngliche Benachrichtigung wird automatisch als gelesen markiert, sobald der Dienstleister ein Angebot abgibt. Dies sorgt für eine saubere Benutzeroberfläche ohne veraltete "Aktion erforderlich" Meldungen.

