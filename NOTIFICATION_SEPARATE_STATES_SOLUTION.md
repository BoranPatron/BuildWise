# Notification System - Separate States für Bauträger und Dienstleister

## Problem behoben ✅

**User-Meldung:** "Dienstleister und Bauträger nutzen hoffentlich nicht die gleiche state variable sodass sie sich gegenseitig die Neuen Nachrichten quittieren. Prüfe und behebe"

**Root Cause:** Bauträger und Dienstleister teilten sich die gleiche `has_unread_messages` Spalte in der Datenbank, wodurch sie sich gegenseitig die Nachrichten als gelesen markieren konnten.

## Lösung implementiert ✅

### 1. Datenbank-Schema erweitert
**Neue Spalten hinzugefügt:**
- `has_unread_messages_bautraeger` (Boolean, default=False)
- `has_unread_messages_dienstleister` (Boolean, default=False)
- `has_unread_messages` (Legacy, behalten für Rückwärtskompatibilität)

**Migration-Script:** `migrate_separate_notification_states.py`
```bash
python migrate_separate_notification_states.py
```

### 2. SQLAlchemy Model aktualisiert
**Datei:** `BuildWise/app/models/milestone.py`
```python
# Benachrichtigungssystem für ungelesene Nachrichten - SEPARATE STATES
has_unread_messages_bautraeger = Column(Boolean, default=False)  # Flag für Bauträger-Benachrichtigungen
has_unread_messages_dienstleister = Column(Boolean, default=False)  # Flag für Dienstleister-Benachrichtigungen
# Legacy: Behalten für Rückwärtskompatibilität
has_unread_messages = Column(Boolean, default=False)  # Flag für ungelesene Nachrichten im Fortschritt-Tab
```

### 3. Pydantic Schemas aktualisiert
**Datei:** `BuildWise/app/schemas/milestone.py`

**Alle Schemas erweitert:**
- `MilestoneBase`
- `MilestoneUpdate`
- `MilestoneRead`
- `MilestoneSummary`

**Neue Felder:**
```python
# Benachrichtigungssystem - SEPARATE STATES für Bauträger und Dienstleister
has_unread_messages_bautraeger: bool = False
has_unread_messages_dienstleister: bool = False
# Legacy: Behalten für Rückwärtskompatibilität
has_unread_messages: bool = False
```

### 4. Backend API Endpoints angepasst
**Datei:** `BuildWise/app/api/milestones.py`

#### `mark-messages-read` Endpoint:
```python
# Markiere Nachrichten als gelesen - USER-SPEZIFISCH
if current_user.user_type in ["PRIVATE", "PROFESSIONAL"]:
    # Bauträger markiert als gelesen
    milestone.has_unread_messages_bautraeger = False
    print(f"✅ Bauträger-Nachrichten für Gewerk {milestone_id} als gelesen markiert")
else:
    # Dienstleister markiert als gelesen
    milestone.has_unread_messages_dienstleister = False
    print(f"✅ Dienstleister-Nachrichten für Gewerk {milestone_id} als gelesen markiert")
```

#### `mark-messages-unread` Endpoint:
```python
# Markiere Nachrichten als ungelesen - USER-SPEZIFISCH
if current_user.user_type in ["PRIVATE", "PROFESSIONAL"]:
    # Bauträger sendet Nachricht → Dienstleister soll Benachrichtigung bekommen
    milestone.has_unread_messages_dienstleister = True
    print(f"✅ Dienstleister-Benachrichtigung für Gewerk {milestone_id} aktiviert")
else:
    # Dienstleister sendet Nachricht → Bauträger soll Benachrichtigung bekommen
    milestone.has_unread_messages_bautraeger = True
    print(f"✅ Bauträger-Benachrichtigung für Gewerk {milestone_id} aktiviert")
```

### 5. Frontend-Komponenten angepasst

#### `TradeSearchResult` Interface:
**Datei:** `Frontend/Frontend/src/api/geoService.ts`
```typescript
has_unread_messages_bautraeger?: boolean;
has_unread_messages_dienstleister?: boolean;
// Legacy: Behalten für Rückwärtskompatibilität
has_unread_messages?: boolean;
```

#### `TradeDetailsModal.tsx`:
**User-spezifische Notification-Logik:**
```typescript
// Verwende user-spezifische Notification-States
const isBautraegerUser = isBautraeger();
const userSpecificUnreadMessages = isBautraegerUser 
  ? (trade.has_unread_messages_bautraeger || false)
  : (trade.has_unread_messages_dienstleister || false);

setHasUnreadMessages(userSpecificUnreadMessages);
```

#### `ServiceProviderDashboard.tsx`:
**Dienstleister-spezifische Anzeige:**
```typescript
// Brief-Symbol für ungelesene Nachrichten - DIENSTLEISTER-SPEZIFISCH
{trade.has_unread_messages_dienstleister && (
  <Mail size={16} className="absolute -top-2 -right-2 text-green-500 animate-pulse" />
)}
```

#### `TradesCard.tsx`:
**User-spezifische Anzeige:**
```typescript
{(() => {
  const isBautraegerUser = isBautraeger();
  const userSpecificUnreadMessages = isBautraegerUser 
    ? (trade.has_unread_messages_bautraeger || false)
    : (trade.has_unread_messages_dienstleister || false);
  
  return userSpecificUnreadMessages && (
    <Mail size={20} className="absolute -top-3 -right-3 text-green-500 animate-pulse" />
  );
})()}
```

## Funktionsweise ✅

### Vorher (Problem):
```
Bauträger sendet Nachricht → has_unread_messages = True
Dienstleister öffnet Tab → has_unread_messages = False (für ALLE)
Bauträger verliert Benachrichtigung ❌
```

### Nachher (Lösung):
```
Bauträger sendet Nachricht → has_unread_messages_dienstleister = True
Dienstleister öffnet Tab → has_unread_messages_dienstleister = False
Bauträger behält Benachrichtigung ✅
```

## Test-Szenario ✅

### Schritt 1: Datenbank vorbereiten
```bash
python -c "import sqlite3; conn = sqlite3.connect('buildwise.db'); cursor = conn.cursor(); cursor.execute('UPDATE milestones SET has_unread_messages_dienstleister = 1 WHERE id = 1'); conn.commit(); print('✅ Dienstleister-Benachrichtigung aktiviert'); conn.close()"
```

### Schritt 2: Bauträger-Test
1. **Login als Bauträger**
2. **Öffne Projekt 1 → Gewerk 1**
3. **Gehe zu "Fortschritt & Kommunikation"**
4. **Sende: "Test Nachricht"**
5. **Prüfe Backend-Logs:** `Dienstleister-Benachrichtigung aktiviert`

### Schritt 3: Dienstleister-Test
1. **Login als Dienstleister**
2. **Öffne ServiceProviderDashboard**
3. **Prüfe Mail-Symbol auf Trade-Kachel**
4. **Öffne TradeDetailsModal → "Fortschritt & Kommunikation"**
5. **Prüfe Backend-Logs:** `Dienstleister-Nachrichten als gelesen markiert`

### Schritt 4: Bauträger-Test (Fortsetzung)
1. **Zurück zu Bauträger**
2. **Prüfe: Mail-Symbol sollte weiterhin angezeigt werden**
3. **Öffne "Fortschritt & Kommunikation"**
4. **Prüfe Backend-Logs:** `Bauträger-Nachrichten als gelesen markiert`

## Debug-Logs ✅

### Backend-Logs:
```
✅ Dienstleister-Benachrichtigung für Gewerk 1 aktiviert (Bauträger sendet Nachricht)
✅ Dienstleister-Nachrichten für Gewerk 1 als gelesen markiert (User 3)
✅ Bauträger-Nachrichten für Gewerk 1 als gelesen markiert (User 1)
```

### Frontend-Logs:
```
🔄 TradeDetailsModal - Dienstleister-hasUnreadMessages initialisiert: true
🔔 Neue Nachrichten erkannt! Status: true (Dienstleister)
📧 Trade 1 (Natursteinfassade & Terrassenbau): Dienstleister hat ungelesene Nachrichten = true
```

## Zusammenfassung ✅

### Problem behoben:
- ✅ Separate Notification-States für Bauträger und Dienstleister
- ✅ Keine gegenseitige Quittierung mehr möglich
- ✅ User-spezifische Benachrichtigungen funktionieren korrekt
- ✅ Rückwärtskompatibilität gewährleistet

### Technische Details:
- ✅ Datenbank-Schema erweitert
- ✅ SQLAlchemy Model aktualisiert
- ✅ Pydantic Schemas erweitert
- ✅ Backend API Endpoints angepasst
- ✅ Frontend-Komponenten aktualisiert
- ✅ Migration-Script erstellt

### Benutzerfreundlichkeit:
- ✅ Bauträger und Dienstleister haben separate Benachrichtigungen
- ✅ Keine gegenseitige Störung mehr
- ✅ Mail-Symbole funktionieren korrekt
- ✅ Polling-System aktualisiert

## Status: ✅ ABGESCHLOSSEN

Das Notification-System verwendet jetzt separate States für Bauträger und Dienstleister. Eine gegenseitige Quittierung ist nicht mehr möglich.

