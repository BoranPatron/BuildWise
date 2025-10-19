# Benachrichtigungssystem für ungelesene Nachrichten

## Übersicht

Das Benachrichtigungssystem ermöglicht es Bauträgern, zu erkennen, wenn Dienstleister neue Nachrichten im "Fortschritt & Kontrolle" Tab abgesetzt haben. Der Tab blinkt solange, bis der Bauträger ihn öffnet und die Nachrichten als gelesen markiert.

## Implementierung

### Backend

#### 1. Datenbank-Erweiterung
- **Neue Spalte**: `has_unread_messages` (BOOLEAN, DEFAULT FALSE) in der `milestones` Tabelle
- **Migration**: `add_unread_messages_to_milestones.py` fügt die Spalte hinzu

#### 2. Model-Erweiterung
- **Milestone Model**: Neue Spalte `has_unread_messages` hinzugefügt
- **Schema-Erweiterung**: Alle relevanten Schemas (MilestoneBase, MilestoneRead, MilestoneSummary) erweitert

#### 3. API-Endpoints
- **POST** `/milestones/{milestone_id}/mark-messages-read`
  - Markiert Nachrichten als gelesen (nur für Bauträger)
  - Setzt `has_unread_messages = false`
  
- **POST** `/milestones/{milestone_id}/mark-messages-unread`
  - Markiert Nachrichten als ungelesen
  - Setzt `has_unread_messages = true`
  - Wird automatisch aufgerufen wenn Dienstleister eine Nachricht sendet

### Frontend

#### 1. TradeDetailsModal Erweiterungen
- **State Management**: `hasUnreadMessages` State für ungelesene Nachrichten
- **Tab-Animation**: Blink-Animation für den "Fortschritt & Kontrolle" Tab
- **Automatisches Markieren**: Nachrichten werden als gelesen markiert, wenn Bauträger den Tab öffnet

#### 2. TradeProgress Erweiterungen
- **Automatische Markierung**: Dienstleister-Nachrichten markieren automatisch als ungelesen
- **API-Integration**: Ruft `/mark-messages-unread` Endpoint auf

#### 3. CSS-Animationen
- **Benutzerdefinierte Animationen**: Subtile Blink-Effekte für bessere UX
- **Klassen**: `tab-notification-blink`, `dot-notification-blink`

## Workflow

### Dienstleister sendet Nachricht
1. Dienstleister schreibt Nachricht im TradeProgress Component
2. Nachricht wird gespeichert
3. Automatisch wird `/mark-messages-unread` aufgerufen
4. `has_unread_messages = true` wird gesetzt

### Bauträger sieht Benachrichtigung
1. Bauträger öffnet TradeDetailsModal
2. `has_unread_messages` wird aus dem Trade-Objekt geladen
3. "Fortschritt & Kontrolle" Tab blinkt mit roter Animation
4. Roter Punkt erscheint neben dem Tab-Namen

### Bauträger öffnet Tab
1. Bauträger klickt auf "Fortschritt & Kontrolle" Tab
2. `handleTabChange('progress')` wird aufgerufen
3. Automatisch wird `/mark-messages-read` aufgerufen
4. `has_unread_messages = false` wird gesetzt
5. Blink-Animation stoppt

## Technische Details

### Berechtigungen
- **Markieren als ungelesen**: Alle Benutzer (wird automatisch aufgerufen)
- **Markieren als gelesen**: Nur Bauträger (PRIVATE, PROFESSIONAL)

### Animationen
- **Tab-Button**: Subtile Puls-Animation mit Schatten-Effekt
- **Roter Punkt**: Schnellere Puls-Animation für Aufmerksamkeit
- **CSS-Klassen**: Benutzerdefinierte Animationen für bessere Kontrolle

### Fehlerbehandlung
- API-Fehler beim Markieren blockieren nicht den normalen Workflow
- Fallback-Werte für fehlende `has_unread_messages` Felder
- Graceful Degradation wenn Backend nicht verfügbar

## Verwendung

Das System funktioniert automatisch ohne zusätzliche Konfiguration:

1. **Dienstleister**: Senden normal Nachrichten - System markiert automatisch als ungelesen
2. **Bauträger**: Sehen blinkende Tabs - System markiert automatisch als gelesen beim Öffnen

## Erweiterungsmöglichkeiten

- **Push-Benachrichtigungen**: WebSocket-Integration für Echtzeit-Updates
- **E-Mail-Benachrichtigungen**: Automatische E-Mails bei neuen Nachrichten
- **Mobile Push**: Integration mit mobilen Push-Benachrichtigungen
- **Benachrichtigungs-Historie**: Tracking von gelesenen/ungelesenen Nachrichten
- **Benutzer-Präferenzen**: Individuelle Benachrichtigungseinstellungen
