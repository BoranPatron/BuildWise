# Benachrichtigungssystem Debug-Anleitung

## Problem
Der Dienstleister sieht keine Benachrichtigung im TradeDetailsModal, obwohl der Bauträger eine Nachricht gesendet hat.

## Aktueller Status
- ✅ Backend: `has_unread_messages` Feld existiert in der Datenbank
- ✅ Backend: API-Endpoints funktionieren (`mark-messages-read`, `mark-messages-unread`)
- ✅ Frontend: Mail-Symbol ist implementiert (TradeDetailsModal, ServiceProviderDashboard, TradesCard)
- ❌ **Problem**: Datenbank zeigt `has_unread_messages = 0` für Milestone 1

## Debug-Schritte

### 1. Prüfen Sie die Browser-Konsole (Bauträger)
Wenn der Bauträger eine Nachricht sendet, sollten Sie folgende Logs sehen:

```
🔍 [NOTIFICATION] Prüfe ob Benachrichtigung gesendet werden soll: {
  isServiceProvider: false,
  isBautraeger: true,
  condition1: false,
  condition2: true,
  shouldSendNotification: true
}
📧 [NOTIFICATION] Sende Benachrichtigung...
✅ Nachrichten als ungelesen markiert für Dienstleister
```

**Wenn Sie stattdessen sehen:**
```
⚠️ [NOTIFICATION] Benachrichtigung wird NICHT gesendet (Bedingung nicht erfüllt)
```

**Dann ist das Problem:**
- `isBautraeger` ist `false` (sollte `true` sein)
- `isServiceProvider` ist `true` (sollte `false` sein)

### 2. Prüfen Sie die Props von TradeProgress
Die TradeProgress Komponente erhält zwei Props:
- `isBautraeger: boolean` - sollte `true` sein für Bauträger
- `isServiceProvider: boolean` - sollte `false` sein für Bauträger

**Prüfen Sie in TradeDetailsModal:**
```typescript
<TradeProgress
  milestoneId={trade.id}
  currentProgress={trade.progress_percentage || 0}
  onProgressChange={handleProgressChange}
  isBautraeger={isBautraeger()}  // <-- Sollte true sein für Bauträger
  isServiceProvider={!isBautraeger()}  // <-- Sollte false sein für Bauträger
  completionStatus={completionStatus}
  onCompletionRequest={handleCompletionRequest}
  onCompletionResponse={handleCompletionResponse}
  hasAcceptedQuote={!!acceptedQuote}
/>
```

### 3. Prüfen Sie die Datenbank
```bash
python -c "import sqlite3; conn = sqlite3.connect('buildwise.db'); cursor = conn.cursor(); result = cursor.execute('SELECT id, title, has_unread_messages FROM milestones WHERE id = 1').fetchone(); print(f'ID: {result[0]}, Title: {result[1]}, has_unread_messages: {result[2]}'); conn.close()"
```

**Erwartetes Ergebnis nach Bauträger-Nachricht:**
```
ID: 1, Title: Natursteinfassade & Terrassenbau, has_unread_messages: 1
```

### 4. Prüfen Sie das Backend-Log
Wenn die Nachricht gesendet wird, sollten Sie im Backend-Log sehen:
```
✅ Nachrichten für Gewerk 1 als ungelesen markiert
```

### 5. Prüfen Sie die API-Response
Nach dem Senden einer Nachricht, laden Sie die Milestones neu:
```bash
# Bauträger Token
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/milestones/?project_id=1" -Headers @{"Authorization"="Bearer YOUR_BAUTRAEGER_TOKEN"} | ConvertTo-Json -Depth 3
```

**Erwartetes Ergebnis:**
```json
{
  "id": 1,
  "has_unread_messages": true
}
```

## Mögliche Lösungen

### Lösung 1: Props sind vertauscht
Wenn `isBautraeger` und `isServiceProvider` vertauscht sind, ändern Sie in TradeDetailsModal:

**FALSCH:**
```typescript
<TradeProgress
  isBautraeger={!isBautraeger()}
  isServiceProvider={isBautraeger()}
/>
```

**RICHTIG:**
```typescript
<TradeProgress
  isBautraeger={isBautraeger()}
  isServiceProvider={!isBautraeger()}
/>
```

### Lösung 2: Bedingung ist zu strikt
Wenn die Bedingung nie erfüllt wird, ändern Sie in TradeProgress.tsx:

**ALT:**
```typescript
if ((isServiceProvider && !isBautraeger) || (isBautraeger && !isServiceProvider)) {
```

**NEU (einfacher):**
```typescript
// Immer Benachrichtigung senden (Backend filtert schon)
try {
  await apiCall(`/milestones/${milestoneId}/mark-messages-unread`, {
    method: 'POST'
  });
  console.log('✅ Benachrichtigung gesendet');
} catch (error) {
  console.error('❌ Fehler:', error);
}
```

### Lösung 3: API-Call schlägt fehl
Wenn der API-Call einen Fehler wirft, prüfen Sie:
- Token ist gültig
- Backend läuft
- CORS ist korrekt konfiguriert

## Test-Szenario

### Schritt 1: Bauträger sendet Nachricht
1. Login als Bauträger
2. Öffne Projekt 1
3. Öffne Gewerk 1 (Natursteinfassade & Terrassenbau)
4. Gehe zu "Fortschritt & Kommunikation" Tab
5. Sende eine Nachricht: "Test Nachricht vom Bauträger"
6. **Prüfe Browser-Konsole** für Debug-Logs

### Schritt 2: Prüfe Datenbank
```bash
python -c "import sqlite3; conn = sqlite3.connect('buildwise.db'); cursor = conn.cursor(); result = cursor.execute('SELECT id, title, has_unread_messages FROM milestones WHERE id = 1').fetchone(); print(f'has_unread_messages: {result[2]}'); conn.close()"
```

**Erwartetes Ergebnis:** `has_unread_messages: 1`

### Schritt 3: Dienstleister prüft Benachrichtigung
1. Login als Dienstleister
2. Öffne ServiceProviderDashboard
3. **Prüfe:** Grünes Mail-Symbol auf Gewerk-Kachel
4. Klicke auf Gewerk
5. **Prüfe:** Grünes Mail-Symbol im "Fortschritt & Kommunikation" Tab
6. Klicke auf Tab
7. **Prüfe:** Mail-Symbol verschwindet

## Debug-Logs entfernen
Nach dem Debugging können Sie die Debug-Logs entfernen oder auskommentieren:

```typescript
// In TradeProgress.tsx, Zeile 188-194 und 209
// console.log('🔍 [NOTIFICATION] ...'); // Auskommentieren
```

## Weitere Informationen
- Siehe `NOTIFICATION_SYSTEM_DOKUMENTATION.md` für vollständige Systemdokumentation
- Backend API: `/api/v1/milestones/{milestone_id}/mark-messages-unread`
- Frontend Komponenten: `TradeProgress.tsx`, `TradeDetailsModal.tsx`, `ServiceProviderDashboard.tsx`, `TradesCard.tsx`

