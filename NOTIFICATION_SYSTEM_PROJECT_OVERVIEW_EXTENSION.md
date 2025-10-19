# Dokumentation: Erweiterung des Benachrichtigungssystems für die Projektübersicht

## 1. Überblick
Dieses Dokument beschreibt die Erweiterung des bestehenden Benachrichtigungssystems für ungelesene Nachrichten, um es auch in der Projektübersicht (Dashboard) zu unterstützen. Bauträger können jetzt direkt in der Gewerk-Übersicht sehen, welche Gewerke neue Nachrichten haben.

## 2. Frontend-Erweiterungen

### 2.1 Trade Interface Erweiterung (`Frontend/Frontend/src/components/TradesCard.tsx`)
Das `Trade` Interface wurde um das `has_unread_messages` Feld erweitert:

```typescript
interface Trade {
  id: number;
  title: string;
  description: string;
  status: 'planned' | 'in_progress' | 'completed' | 'delayed' | 'cancelled';
  contractor?: string;
  start_date?: string;
  end_date?: string;
  budget?: number;
  actual_costs?: number;
  progress_percentage: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  category?: string;
  notes?: string;
  planned_date?: string;
  requires_inspection?: boolean;
  created_at: string;
  updated_at: string;
  // Benachrichtigungssystem für ungelesene Nachrichten
  has_unread_messages?: boolean;
}
```

### 2.2 Visueller Indikator in TradesCard
Ein kleiner roter Punkt mit Blinkanimation wurde zum Wrench-Icon hinzugefügt, um ungelesene Nachrichten anzuzeigen:

```typescript
<div className="relative">
  <div className="p-2 bg-[#ffbd59]/20 rounded-lg">
    <Wrench size={16} className="text-[#ffbd59]" />
  </div>
  {/* Benachrichtigungs-Indikator für ungelesene Nachrichten */}
  {trade.has_unread_messages && (
    <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white/20 dot-notification-blink"></div>
  )}
</div>
```

### 2.3 CSS-Animation
Die bereits vorhandene `dot-notification-blink` CSS-Klasse aus `notification-animations.css` wird verwendet:

```css
@keyframes dot-blink {
  0%, 100% {
    opacity: 0.5;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}

.dot-notification-blink {
  animation: dot-blink 1.5s ease-in-out infinite;
}
```

## 3. Backend-Integration

### 3.1 Automatische Datenübertragung
Das Backend liefert bereits die `has_unread_messages` Daten über die bestehenden API-Endpunkte:
- `GET /milestones` (für Projekt-Gewerke)
- `GET /milestones/{id}` (für einzelne Gewerke)

### 3.2 Datenfluss
1. **Dienstleister sendet Nachricht** → `has_unread_messages = true` wird gesetzt
2. **Dashboard lädt Gewerke** → `has_unread_messages` wird mit übertragen
3. **TradesCard zeigt Indikator** → Roter Punkt blinkt bei `has_unread_messages = true`
4. **Bauträger öffnet Gewerk** → `has_unread_messages = false` wird gesetzt

## 4. Funktionsweise

### 4.1 Anzeige in der Projektübersicht
- **Ort:** Dashboard → Gewerk-Sektion → TradesCard
- **Indikator:** Kleiner roter Punkt mit Blinkanimation am Wrench-Icon
- **Bedingung:** Nur sichtbar wenn `trade.has_unread_messages === true`

### 4.2 Benutzerinteraktion
- **Klick auf Gewerk:** Öffnet TradeDetailsModal
- **Automatisches Zurücksetzen:** Beim Öffnen des "Fortschritt & Kommunikation"-Tabs wird der Status zurückgesetzt
- **Persistierung:** Status wird in der Datenbank gespeichert

## 5. Vorteile der Erweiterung

### 5.1 Verbesserte Benutzerfreundlichkeit
- **Schnelle Übersicht:** Bauträger sehen sofort, welche Gewerke neue Nachrichten haben
- **Keine verpassten Nachrichten:** Visueller Indikator verhindert das Übersehen wichtiger Kommunikation
- **Konsistente UX:** Gleiche Benachrichtigungslogik in Detail- und Übersichtsansicht

### 5.2 Technische Vorteile
- **Wiederverwendung:** Nutzt bestehende CSS-Animationen und Backend-Logik
- **Minimaler Code:** Nur wenige Zeilen Code für große Verbesserung
- **Skalierbar:** Funktioniert mit beliebig vielen Gewerken

## 6. Test-Szenarien

### 6.1 Szenario 1: Neue Nachricht von Dienstleister
1. Bauträger ist im Dashboard
2. Dienstleister sendet Nachricht in einem Gewerk
3. **Erwartung:** Roter Punkt erscheint am entsprechenden Gewerk-Icon
4. **Verifikation:** `has_unread_messages = true` in der Datenbank

### 6.2 Szenario 2: Nachricht wird gelesen
1. Bauträger sieht blinkenden roten Punkt
2. Bauträger klickt auf das Gewerk
3. Bauträger öffnet "Fortschritt & Kommunikation"-Tab
4. **Erwartung:** Roter Punkt verschwindet
5. **Verifikation:** `has_unread_messages = false` in der Datenbank

### 6.3 Szenario 3: Mehrere Gewerke mit Nachrichten
1. Mehrere Dienstleister senden Nachrichten in verschiedenen Gewerken
2. **Erwartung:** Mehrere rote Punkte blinken gleichzeitig
3. **Verifikation:** Jeder Punkt verschwindet einzeln beim Lesen

## 7. Kompatibilität

### 7.1 Bestehende Funktionalität
- **Keine Breaking Changes:** Alle bestehenden Features funktionieren weiterhin
- **Rückwärtskompatibel:** Gewerke ohne `has_unread_messages` zeigen keinen Indikator
- **Graceful Degradation:** Bei API-Fehlern wird kein Indikator angezeigt

### 7.2 Browser-Unterstützung
- **CSS-Animationen:** Unterstützt von allen modernen Browsern
- **JavaScript:** Nutzt Standard React-Patterns
- **Responsive Design:** Funktioniert auf Desktop und Mobile

## 8. Wartung und Erweiterungen

### 8.1 Zukünftige Erweiterungen
- **Push-Benachrichtigungen:** Integration mit Browser-Notifications
- **E-Mail-Benachrichtigungen:** Automatische E-Mails bei neuen Nachrichten
- **Benachrichtigungszentrale:** Zentrale Übersicht aller Benachrichtigungen

### 8.2 Monitoring
- **Logs:** Backend protokolliert alle Status-Änderungen
- **Debugging:** Console-Logs im Frontend für Entwicklung
- **Performance:** Minimale Auswirkung auf Ladezeiten

## 9. Zusammenfassung

Die Erweiterung des Benachrichtigungssystems für die Projektübersicht bietet eine nahtlose Integration in das bestehende System. Mit minimalen Code-Änderungen wird eine erhebliche Verbesserung der Benutzerfreundlichkeit erreicht. Bauträger können jetzt effizienter kommunizieren und verpassen keine wichtigen Nachrichten von Dienstleistern.

**Implementierte Features:**
- ✅ Visueller Indikator für ungelesene Nachrichten in der Projektübersicht
- ✅ Automatisches Zurücksetzen beim Lesen der Nachrichten
- ✅ Konsistente Benachrichtigungslogik zwischen Detail- und Übersichtsansicht
- ✅ Responsive Design für alle Geräte
- ✅ Vollständige Backend-Integration
