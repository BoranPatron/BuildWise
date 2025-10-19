# Benachrichtigungs-Polling System - Implementierung

## Problem
Der Dienstleister sah keine Benachrichtigung im TradeDetailsModal, obwohl der Bauträger eine Nachricht gesendet hatte. Die Datenbank wurde korrekt aktualisiert (`has_unread_messages = 1`), aber der Dienstleister musste die Seite manuell neu laden, um die Benachrichtigung zu sehen.

## Root Cause
Das Frontend lädt die Milestone-Daten nur beim initialen Mount der Komponente. Wenn der Dienstleister das TradeDetailsModal **bereits offen** hat und der Bauträger eine neue Nachricht sendet, wird der `has_unread_messages` Status im Frontend nicht automatisch aktualisiert.

## Lösung: Polling-System

### 1. TradeDetailsModal.tsx - Real-Time Notification Updates
**Datei:** `Frontend/Frontend/src/components/TradeDetailsModal.tsx`

**Implementierung:**
```typescript
// Polling: Prüfe alle 10 Sekunden auf neue Nachrichten
useEffect(() => {
  if (!isOpen || !trade?.id) return;
  
  const checkForNewMessages = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch(`${getApiBaseUrl()}/milestones/${trade.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const newStatus = data.has_unread_messages || false;
        
        if (newStatus !== hasUnreadMessages) {
          console.log('🔔 Neue Nachrichten erkannt! Status:', newStatus);
          setHasUnreadMessages(newStatus);
        }
      }
    } catch (error) {
      console.error('❌ Fehler beim Prüfen auf neue Nachrichten:', error);
    }
  };
  
  // Starte Polling alle 10 Sekunden
  const intervalId = setInterval(checkForNewMessages, 10000);
  
  // Cleanup: Stoppe Polling wenn Modal geschlossen wird
  return () => clearInterval(intervalId);
}, [isOpen, trade?.id, hasUnreadMessages]);
```

**Funktionsweise:**
- ✅ Prüft alle **10 Sekunden**, ob neue Nachrichten vorhanden sind
- ✅ Läuft nur, wenn das Modal **geöffnet** ist
- ✅ Stoppt automatisch, wenn das Modal **geschlossen** wird
- ✅ Aktualisiert nur den `hasUnreadMessages` State, nicht die gesamte Komponente

**Vorteile:**
- **Real-Time Updates**: Dienstleister sieht Benachrichtigungen innerhalb von 10 Sekunden
- **Performant**: Nur ein kleiner API-Call alle 10 Sekunden
- **Ressourcenschonend**: Polling stoppt, wenn Modal geschlossen ist
- **Automatisches Cleanup**: Kein Memory Leak durch `clearInterval`

### 2. ServiceProviderDashboard.tsx - Trade Card Updates
**Datei:** `Frontend/Frontend/src/pages/ServiceProviderDashboard.tsx`

**Implementierung:**
```typescript
// Zusätzlicher useEffect für regelmäßige Aktualisierung der Service Provider Quotes und Trades
useEffect(() => {
  if (!user) return;
  
  const refreshServiceProviderData = () => {
    console.log('🔄 Regelmäßige Aktualisierung der Service Provider Daten...');
    
    // Aktualisiere Quotes
    loadServiceProviderQuotes().catch(error => {
      console.error('❌ Fehler bei regelmäßiger Aktualisierung (Quotes):', error);
    });
    
    // Aktualisiere Trades (für has_unread_messages)
    loadTrades().catch(error => {
      console.error('❌ Fehler bei regelmäßiger Aktualisierung (Trades):', error);
    });
  };
  
  // Sofortige Aktualisierung
  refreshServiceProviderData();
  
  // Dann alle 30 Sekunden
  const interval = setInterval(refreshServiceProviderData, 30000);
  
  return () => clearInterval(interval);
}, [user?.id]);
```

**Funktionsweise:**
- ✅ Prüft alle **30 Sekunden**, ob neue Nachrichten in den Trade-Karten vorhanden sind
- ✅ Lädt sowohl Quotes als auch Trades neu
- ✅ Zeigt grünes Mail-Symbol auf Trade-Karten, wenn `has_unread_messages = true`

**Vorteile:**
- **Dashboard bleibt aktuell**: Dienstleister sieht neue Nachrichten in der Übersicht
- **Moderate Polling-Frequenz**: 30 Sekunden ist ein guter Kompromiss zwischen Performance und Aktualität
- **Läuft nur bei angemeldetem User**: `if (!user) return`

## Ablauf bei neuer Nachricht

### Szenario: Bauträger sendet Nachricht an Dienstleister

1. **Bauträger sendet Nachricht** (TradeProgress.tsx)
   ```
   📧 Bauträger: "Test Nachricht"
   ↓
   POST /api/v1/milestones/1/progress/
   ↓
   POST /api/v1/milestones/1/mark-messages-unread
   ↓
   ✅ DB: has_unread_messages = 1
   ```

2. **Dienstleister hat TradeDetailsModal offen**
   ```
   ⏱️ Nach max. 10 Sekunden:
   GET /api/v1/milestones/1
   ↓
   🔔 Neue Nachrichten erkannt!
   ↓
   setHasUnreadMessages(true)
   ↓
   📧 Grünes Mail-Symbol erscheint im Tab
   ```

3. **Dienstleister ist auf Dashboard**
   ```
   ⏱️ Nach max. 30 Sekunden:
   loadTrades()
   ↓
   GET /api/v1/milestones/
   ↓
   🔄 Trade-Liste aktualisiert
   ↓
   📧 Grünes Mail-Symbol erscheint auf Trade-Karte
   ```

4. **Dienstleister klickt auf "Fortschritt & Kommunikation" Tab**
   ```
   🔄 Tab-Wechsel zu "progress"
   ↓
   markMessagesAsRead()
   ↓
   POST /api/v1/milestones/1/mark-messages-read
   ↓
   ✅ DB: has_unread_messages = 0
   ↓
   setHasUnreadMessages(false)
   ↓
   📧 Mail-Symbol verschwindet
   ```

## Polling-Intervalle

### Warum unterschiedliche Intervalle?

| Komponente | Intervall | Grund |
|------------|-----------|-------|
| **TradeDetailsModal** | 10 Sekunden | User schaut aktiv auf das Gewerk, erwartet schnelle Updates |
| **ServiceProviderDashboard** | 30 Sekunden | User ist in der Übersicht, moderate Aktualität ausreichend |

### Performance-Überlegungen

**TradeDetailsModal (10 Sekunden):**
- API-Call: `GET /api/v1/milestones/{id}` → ~50-200ms
- Pro Stunde: 360 Requests
- Impact: Minimal, da nur läuft wenn Modal offen

**ServiceProviderDashboard (30 Sekunden):**
- API-Call: `GET /api/v1/milestones/` → ~200-500ms
- Pro Stunde: 120 Requests
- Impact: Minimal, da nur für angemeldete Dienstleister

## Alternative: WebSockets (Zukunft)

Für eine noch bessere Performance könnte in Zukunft WebSockets implementiert werden:

```typescript
// Beispiel für WebSocket-Integration
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'new_message' && data.milestone_id === trade.id) {
    setHasUnreadMessages(true);
  }
};
```

**Vorteile von WebSockets:**
- ✅ **Instant Updates**: Keine Verzögerung
- ✅ **Server Push**: Server sendet nur bei Änderung
- ✅ **Weniger API-Calls**: Nur bei tatsächlichen Updates

**Nachteile:**
- ❌ **Komplexere Implementierung**: Erfordert WebSocket-Server
- ❌ **Connection Management**: Reconnection-Logic notwendig
- ❌ **Firewall-Probleme**: Manche Firmen blockieren WebSockets

## Testing

### Manueller Test

1. **Login als Bauträger** (Browser 1)
   - Öffne Projekt 1
   - Öffne Gewerk 1
   - Gehe zu "Fortschritt & Kommunikation"

2. **Login als Dienstleister** (Browser 2)
   - Öffne ServiceProviderDashboard
   - Warte auf Dashboard (Trade-Karten sichtbar)
   - **ODER** öffne Gewerk 1 Modal

3. **Bauträger sendet Nachricht** (Browser 1)
   - Sende: "Test Nachricht vom Bauträger"
   - Prüfe Console: `✅ Nachrichten als ungelesen markiert`

4. **Dienstleister prüft Benachrichtigung** (Browser 2)
   - **Dashboard**: Warte max. 30 Sekunden → 📧 Grünes Mail-Symbol auf Trade-Karte
   - **Modal offen**: Warte max. 10 Sekunden → 📧 Grünes Mail-Symbol im Tab

5. **Dienstleister klickt auf Tab** (Browser 2)
   - Klicke "Fortschritt & Kommunikation"
   - Prüfe: Mail-Symbol verschwindet

### Console-Logs prüfen

**TradeDetailsModal:**
```
🔄 TradeDetailsModal - hasUnreadMessages initialisiert: false
🔔 Neue Nachrichten erkannt! Status: true
🔄 hasUnreadMessages geändert zu: true
📧 Fortschritt-Tab geöffnet mit ungelesenen Nachrichten - markiere als gelesen
✅ Nachrichten als gelesen markiert für Dienstleister - hasUnreadMessages auf false gesetzt
```

**ServiceProviderDashboard:**
```
🔄 Regelmäßige Aktualisierung der Service Provider Daten...
🔍 loadTrades: Milestones geladen: 5 Trades
```

## Zusammenfassung

✅ **Problem gelöst**: Dienstleister sieht jetzt Benachrichtigungen in Echtzeit (max. 10-30 Sekunden Verzögerung)

✅ **Implementiert**:
- Polling im TradeDetailsModal (10 Sekunden)
- Polling im ServiceProviderDashboard (30 Sekunden)
- Automatisches Cleanup bei Komponenten-Unmount

✅ **Funktioniert für**:
- Bauträger → Dienstleister Nachrichten
- Dienstleister → Bauträger Nachrichten
- TradeDetailsModal
- ServiceProviderDashboard
- TradesCard (in Projektübersicht)

✅ **Performance**:
- Minimal overhead (kleine API-Calls)
- Polling stoppt bei geschlossenem Modal
- Moderate Polling-Intervalle

🔮 **Zukunft**: WebSocket-Integration für instant Updates

