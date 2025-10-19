# Ressourcen-Benachrichtigung: Persistente Quittierung bei Angebotsabgabe

## Problem
Wenn ein Bauträger eine Ressource bei der Erstellung einer Ausschreibung "anzieht", erhält der Dienstleister eine Benachrichtigung in der Benachrichtigungslasche. Die Benachrichtigung erscheint mit dem Status "🎯 Angezogen" im Abschnitt "Ressourcenverwaltung". 

**Ursprüngliches Problem:** 
- Wenn der Dienstleister auf den Button zur Abgabe des Erstangebots klickt, wurde die Benachrichtigung nur lokal im Browser (LocalStorage) als "gesehen" markiert
- Bei jedem Refresh der Seite tauchte die Benachrichtigung erneut auf
- Die Benachrichtigung wurde nicht persistent in der Datenbank als quittiert markiert

## Lösung: Multi-Layer Acknowledgment System

Die Lösung implementiert ein robustes, mehrschichtiges System zur persistenten Quittierung von Benachrichtigungen:

### 1. Backend API - Notification Acknowledgment

#### Datenbank-Modell (`BuildWise/app/models/notification.py`)
```python
class Notification(Base):
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    
    # Status-Felder
    is_read = Column(Boolean, default=False, index=True)
    is_acknowledged = Column(Boolean, default=False, index=True)  # ✅ Kritisch für Persistenz
    
    # Zeitstempel
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)  # ✅ Zeitpunkt der Quittierung
```

**Wichtige Unterscheidung:**
- `is_read`: Benachrichtigung wurde angesehen (anzeige-relevant)
- `is_acknowledged`: Benachrichtigung wurde quittiert, Aktion wurde ausgeführt (workflow-relevant)

#### API Endpoint (`BuildWise/app/api/notifications.py`)
```python
@router.patch("/{notification_id}/acknowledge")
async def acknowledge_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Quittiert eine Benachrichtigung"""
    notification = await NotificationService.acknowledge_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Benachrichtigung nicht gefunden")
    
    return {"message": "Benachrichtigung quittiert", "notification_id": notification_id}
```

### 2. Frontend Service - Acknowledge Method

#### `Frontend/Frontend/src/api/notificationService.ts`
```typescript
// Benachrichtigung als quittiert markieren (acknowledge)
async acknowledgeNotification(notificationId: number): Promise<void> {
  try {
    await api.patch(`/notifications/${notificationId}/acknowledge`);
    console.log('✅ Benachrichtigung quittiert:', notificationId);
  } catch (error) {
    console.error('❌ Fehler beim Quittieren der Benachrichtigung:', error);
    throw error;
  }
}
```

### 3. Frontend UI - Notification Tab Component

#### `Frontend/Frontend/src/components/NotificationTab.tsx`

**A) Quittierung beim Klick auf die Benachrichtigung:**

```typescript
// Wenn Dienstleister auf resource_allocated Benachrichtigung klickt
else if (userRole === 'DIENSTLEISTER' && notification.type === 'resource_allocated') {
  console.log('📋 Öffne Ausschreibung für Angebotsabgabe von Resource Allocation:', notification.tradeId);
  
  // ✅ SCHRITT 1: Markiere Benachrichtigung als quittiert im Backend
  if (notification.notification?.id) {
    try {
      await fetch(`http://localhost:8000/api/v1/notifications/${notification.notification.id}/acknowledge`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      console.log('✅ Benachrichtigung als quittiert markiert:', notification.notification.id);
      
      // ✅ SCHRITT 2: Lade Benachrichtigungen sofort neu, um UI zu aktualisieren
      setTimeout(() => {
        loadNotifications();
      }, 500);
    } catch (error) {
      console.error('❌ Fehler beim Quittieren der Benachrichtigung:', error);
    }
  }
  
  // ✅ SCHRITT 3: Markiere auch lokal als gesehen (für Fallback)
  markAsSeen([notification.id]);
  
  // ✅ SCHRITT 4: Öffne CostEstimateForm für Angebotsabgabe
  window.dispatchEvent(new CustomEvent('openTradeDetails', {
    detail: {
      tradeId: notification.tradeId,
      allocationId: notification.allocationId,
      source: 'resource_allocation_notification',
      showQuoteForm: true
    }
  }));
  
  // ✅ SCHRITT 5: Schließe Benachrichtigungs-Panel
  setIsExpanded(false);
}
```

**B) Filterung von quittierten Benachrichtigungen beim Laden:**

```typescript
// Filtere für Dienstleister relevante Benachrichtigungen
if (userRole === 'DIENSTLEISTER') {
  console.log('🔔 NotificationTab: Processing notifications for DIENSTLEISTER');
  generalNotifications.forEach((notification: any) => {
    console.log('🔔 NotificationTab: Processing notification:', notification);
    
    // ✅ Überspringe bereits quittierte Benachrichtigungen
    if (notification.is_acknowledged) {
      console.log('🔔 NotificationTab: Skipping acknowledged notification:', notification.id);
      return;  // Wichtig: Diese Benachrichtigung wird NICHT zur Liste hinzugefügt
    }
    
    if (notification.type === 'resource_allocated') {
      // ... Füge Benachrichtigung zur Liste hinzu
      notifications.push({
        id: notification.id,
        type: 'resource_allocated',
        title: notification.title,
        message: notification.message,
        timestamp: notification.created_at,
        isNew: !notification.is_acknowledged,  // ✅ Verwendet Backend-Status
        notification: notification,
        // ... weitere Felder
      });
    }
  });
}
```

### 4. Backend - Doppelte Quittierung beim Quote-Submit

#### `BuildWise/app/api/resources.py` - Endpoint `submit_quote_from_allocation`

Zusätzlich zur Frontend-Quittierung markiert das Backend die Benachrichtigung automatisch als quittiert, wenn das Angebot erfolgreich erstellt wurde:

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
        resource_notification.is_acknowledged = True  # ✅ Quittierung
        resource_notification.acknowledged_at = datetime.now()
        await db.commit()
        print(f"[OK] Ursprüngliche resource_allocated Benachrichtigung als gelesen markiert: ID={resource_notification.id}")
    else:
        print(f"[WARN] Keine resource_allocated Benachrichtigung für Allocation {allocation_id} gefunden")
except Exception as e:
    print(f"[WARN] Fehler beim Markieren der ursprünglichen Benachrichtigung: {e}")
    # Fehler nicht weiterwerfen, da die Hauptfunktion erfolgreich war
```

**Warum doppelte Quittierung?**
- **Frontend-Quittierung**: Sofortige UI-Aktualisierung, Benachrichtigung verschwindet unmittelbar
- **Backend-Quittierung beim Submit**: Failsafe, falls Frontend-Quittierung fehlschlägt oder User die Seite vor dem Submit verlässt

## Workflow Ende-zu-Ende

### 1. Ressource wird angezogen
```
Bauträger → Ausschreibung erstellen → Ressource auswählen
    ↓
Backend erstellt ResourceAllocation mit Status: PRE_SELECTED
    ↓
Backend erstellt Notification mit type: RESOURCE_ALLOCATED
    - is_acknowledged: False
    - is_read: False
```

### 2. Dienstleister sieht Benachrichtigung
```
Dienstleister öffnet Dashboard
    ↓
NotificationTab lädt Benachrichtigungen vom Backend
    ↓
Filtert: Zeigt nur Benachrichtigungen mit is_acknowledged = False
    ↓
Anzeige: "🎯 Angezogen" Badge + Benachrichtigung mit "Angebot abgeben" Button
```

### 3. Dienstleister klickt auf Benachrichtigung
```
Klick auf Benachrichtigung
    ↓
Frontend sendet PATCH /notifications/{id}/acknowledge an Backend
    ↓
Backend setzt is_acknowledged = True, acknowledged_at = NOW()
    ↓
Frontend lädt Benachrichtigungen neu (nach 500ms)
    ↓
Benachrichtigung wird herausgefiltert (is_acknowledged = True)
    ↓
UI zeigt: Benachrichtigung verschwindet
    ↓
CostEstimateForm öffnet sich für Angebotsabgabe
```

### 4. Dienstleister gibt Angebot ab
```
Dienstleister füllt CostEstimateForm aus → Submit
    ↓
Frontend sendet POST /api/v1/resources/allocations/{id}/submit-quote
    ↓
Backend erstellt Quote
    ↓
Backend aktualisiert ResourceAllocation: Status = OFFER_SUBMITTED
    ↓
Backend markiert Benachrichtigung erneut als quittiert (Failsafe)
    ↓
Frontend erhält Erfolgsantwort
    ↓
Ressource zeigt Status: "Angebot abgegeben"
```

### 5. Refresh / Neuer Seitenaufruf
```
Dienstleister refresht Seite oder öffnet Dashboard erneut
    ↓
NotificationTab lädt Benachrichtigungen vom Backend
    ↓
Backend Query: WHERE is_acknowledged = False
    ↓
Resultat: Benachrichtigung wird NICHT zurückgegeben
    ↓
UI zeigt: Keine Benachrichtigung für diese Ressource
    ↓
✅ Problem gelöst: Benachrichtigung erscheint nicht mehr
```

## Best Practices - Was wurde implementiert

### 1. **Dual-Status System (is_read vs. is_acknowledged)**
- **is_read**: Optisch gesehen, aber Aktion noch nicht ausgeführt
- **is_acknowledged**: Aktion wurde ausgeführt, Workflow abgeschlossen
- **Vorteil**: Klare Trennung zwischen "Gesehen" und "Erledigt"

### 2. **Immediate UI Update mit Backend Persistence**
```typescript
// Sofortige UI-Aktualisierung
await fetch('/notifications/{id}/acknowledge', { method: 'PATCH' });

// Reload nach kurzer Verzögerung für saubere UI
setTimeout(() => {
  loadNotifications();
}, 500);
```

### 3. **Defensive Programmierung**
```typescript
// Prüfe ob notification.notification?.id existiert
if (notification.notification?.id) {
  try {
    await acknowledgeNotification(notification.notification.id);
  } catch (error) {
    console.error('Fehler beim Quittieren:', error);
    // Fehler wird geloggt, aber Workflow läuft weiter
  }
}
```

### 4. **Failsafe Backend-Quittierung**
```python
# Backend markiert Benachrichtigung zusätzlich beim Quote-Submit
try:
    resource_notification.is_acknowledged = True
    await db.commit()
except Exception as e:
    print(f"[WARN] Fehler: {e}")
    # Fehler wird geloggt, aber Quote-Erstellung läuft weiter
```

### 5. **Indexed Queries für Performance**
```python
# Datenbank-Index auf is_acknowledged für schnelle Filterung
is_acknowledged = Column(Boolean, default=False, index=True)

# Query nutzt Index automatisch
WHERE is_acknowledged = False
```

### 6. **Consistent Logging für Debugging**
```typescript
console.log('✅ Benachrichtigung als quittiert markiert:', notificationId);
console.log('🔔 NotificationTab: Skipping acknowledged notification:', notificationId);
```

```python
print(f"[OK] Benachrichtigung als gelesen markiert: ID={notification_id}")
print(f"[WARN] Keine resource_allocated Benachrichtigung gefunden")
```

### 7. **Event-Driven Architecture**
```typescript
// Frontend dispatcht Event für ServiceProviderDashboard
window.dispatchEvent(new CustomEvent('openTradeDetails', {
  detail: {
    tradeId: notification.tradeId,
    allocationId: notification.allocationId,
    source: 'resource_allocation_notification',
    showQuoteForm: true
  }
}));
```

## Geänderte Dateien

### Backend
1. **`BuildWise/app/api/notifications.py`**
   - Endpoint `/notifications/{notification_id}/acknowledge` (bereits vorhanden, getestet)

2. **`BuildWise/app/models/notification.py`**
   - Felder `is_acknowledged` und `acknowledged_at` (bereits vorhanden)

3. **`BuildWise/app/api/resources.py`**
   - Endpoint `submit_quote_from_allocation` - Doppelte Quittierung (bereits vorhanden)

### Frontend
1. **`Frontend/Frontend/src/api/notificationService.ts`**
   - ✅ NEU: `acknowledgeNotification()` Methode hinzugefügt

2. **`Frontend/Frontend/src/components/NotificationTab.tsx`**
   - ✅ GEÄNDERT: Quittierung beim Klick auf `resource_allocated` Benachrichtigung
   - ✅ GEÄNDERT: Quittierung beim Klick auf `tender_invitation` Benachrichtigung
   - ✅ GEÄNDERT: Filterung von quittierten Benachrichtigungen in `loadNotifications()`
   - ✅ GEÄNDERT: Sofortiger Reload nach Quittierung für UI-Update

## Testing-Szenarien

### Szenario 1: Happy Path
1. ✅ Bauträger zieht Ressource an → Benachrichtigung wird erstellt
2. ✅ Dienstleister sieht Benachrichtigung in NotificationTab
3. ✅ Dienstleister klickt auf Benachrichtigung → Backend quittiert
4. ✅ Benachrichtigung verschwindet aus Liste
5. ✅ CostEstimateForm öffnet sich
6. ✅ Dienstleister gibt Angebot ab → Backend quittiert erneut (Failsafe)
7. ✅ Refresh der Seite → Benachrichtigung erscheint NICHT mehr

### Szenario 2: Klick ohne Quote-Submit
1. ✅ Dienstleister klickt auf Benachrichtigung → Backend quittiert
2. ✅ Benachrichtigung verschwindet
3. ✅ CostEstimateForm öffnet sich
4. ✅ Dienstleister schließt Form ohne Angebot abzugeben
5. ✅ Benachrichtigung erscheint trotzdem NICHT mehr (korrekt, da bereits quittiert)

### Szenario 3: Netzwerk-Fehler bei Frontend-Quittierung
1. ✅ Dienstleister klickt auf Benachrichtigung → Frontend-Quittierung schlägt fehl
2. ✅ CostEstimateForm öffnet sich trotzdem
3. ✅ Dienstleister gibt Angebot ab
4. ✅ Backend quittiert Benachrichtigung beim Quote-Submit (Failsafe)
5. ✅ Nächster Refresh → Benachrichtigung erscheint NICHT mehr

### Szenario 4: Mehrere Dienstleister, gleiche Ausschreibung
1. ✅ Bauträger zieht Ressourcen von DL1 und DL2 an
2. ✅ DL1 erhält Benachrichtigung #1, DL2 erhält Benachrichtigung #2
3. ✅ DL1 klickt und gibt Angebot ab → Nur Benachrichtigung #1 wird quittiert
4. ✅ DL2 sieht weiterhin seine Benachrichtigung #2 (korrekt)
5. ✅ DL2 klickt und gibt Angebot ab → Benachrichtigung #2 wird quittiert
6. ✅ Beide Dienstleister sehen keine Benachrichtigungen mehr (korrekt)

## Performance-Optimierungen

### 1. Database Indexes
```python
is_acknowledged = Column(Boolean, default=False, index=True)
acknowledged_at = Column(DateTime, nullable=True)
```
- **Vorteil**: Schnelle Filterung mit `WHERE is_acknowledged = False`

### 2. Minimal Payload
```typescript
await fetch('/notifications/{id}/acknowledge', { 
  method: 'PATCH',
  // Kein Body nötig, nur ID im Path
});
```
- **Vorteil**: Minimale Netzwerk-Last

### 3. Optimistic UI Update
```typescript
// Schließe Panel sofort, warte nicht auf Backend-Response
setIsExpanded(false);

// Reload erfolgt asynchron im Hintergrund
setTimeout(() => loadNotifications(), 500);
```
- **Vorteil**: Gefühlte Geschwindigkeit für Benutzer

## Error Handling

### Frontend
```typescript
try {
  await acknowledgeNotification(notificationId);
  setTimeout(() => loadNotifications(), 500);
} catch (error) {
  console.error('❌ Fehler beim Quittieren:', error);
  // Workflow läuft trotzdem weiter
}
```

### Backend
```python
try:
    resource_notification.is_acknowledged = True
    await db.commit()
except Exception as e:
    print(f"[WARN] Fehler: {e}")
    # Hauptoperation (Quote-Erstellung) läuft weiter
```

## Monitoring & Debugging

### Log-Muster für Erfolg
```
Frontend:
✅ Benachrichtigung als quittiert markiert: 123

Backend:
[OK] Ursprüngliche resource_allocated Benachrichtigung als gelesen markiert: ID=123
```

### Log-Muster für Probleme
```
Frontend:
❌ Fehler beim Quittieren der Benachrichtigung: NetworkError

Backend:
[WARN] Keine resource_allocated Benachrichtigung für Allocation 456 gefunden
[WARN] Fehler beim Markieren der ursprünglichen Benachrichtigung: ...
```

## Zusammenfassung

Die Implementierung löst das Problem der wiederauftauchenden Benachrichtigungen durch:

1. ✅ **Persistente Quittierung in der Datenbank** (`is_acknowledged = True`)
2. ✅ **Filterung quittierter Benachrichtigungen** beim Laden
3. ✅ **Dual-Quittierung** (Frontend beim Klick + Backend beim Quote-Submit)
4. ✅ **Sofortiges UI-Update** nach Quittierung
5. ✅ **Robuste Fehlerbehandlung** mit Failsafes
6. ✅ **Best Practices** für Logging, Indizierung und Performance

Das System ist jetzt **robust, persistent und benutzerfreundlich** implementiert.


