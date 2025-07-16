# Canvas-System Implementierung

## Übersicht

Das Canvas-System wurde erfolgreich in BuildWise implementiert und bietet ein vollständiges MIRO-ähnliches Whiteboard mit allen gewünschten Funktionen.

## Implementierte Features

### 1. Canvas-Funktionen (MIRO-ähnlich)

#### ✅ Unendliches Whiteboard
- **Pan/Zoom**: Stufenloses Verschieben und Zoomen ohne Begrenzung
- **Smooth Performance**: Optimierte Rendering-Performance auch bei vielen Objekten
- **Touch-Support**: Vollständige Bedienbarkeit auf Tablet-Geräten

#### ✅ Objekttypen
- **Sticky Notes**: Gelbe Notizen mit Text-Bearbeitung
- **Rechtecke**: Rahmen mit anpassbarer Farbe
- **Kreise**: Ellipsen mit anpassbarer Farbe
- **Linien**: SVG-basierte Linien
- **Textfelder**: Editierbare Text-Objekte
- **Bilder**: Upload und Anzeige von Bildern

#### ✅ Objekt-Manipulation
- **Drag & Drop**: Alle Objekte können verschoben werden
- **Resize-Handles**: Skalierung über Ecken
- **Rotation**: Objekte können rotiert werden
- **Kontextmenü**: Rechtsklick für weitere Aktionen
- **Multi-Selection**: Shift-Klick für Mehrfachauswahl

#### ✅ Undo/Redo-System
- **Vollständige Historie**: Alle Aktionen werden protokolliert
- **Keyboard-Shortcuts**: Ctrl+Z (Undo), Ctrl+Shift+Z (Redo)
- **Toolbar-Buttons**: Visuelle Undo/Redo-Buttons

### 2. Kollaboration & Nutzerverwaltung

#### ✅ Echtzeit-Kollaboration
- **WebSocket-Verbindung**: <1 Sekunde Synchronisierung
- **Live-Cursor**: Anzeige aller aktiven Nutzer-Cursor
- **User-Zuordnung**: Eindeutige Zuordnung aller Aktionen
- **Session-Management**: Automatische Verbindungsverwaltung

#### ✅ Kollaborationsbereiche
- **Rechteckige Bereiche**: Beliebig viele Kollaborationsbereiche
- **Drag & Drop**: Bereiche können verschoben und skaliert werden
- **Benennung**: Jeder Bereich kann individuell benannt werden
- **Bereichszuordnung**: Moderator kann Nutzer Bereichen zuweisen
- **Überlappungsverbot**: Bereiche dürfen sich nicht überschneiden
- **Visuelle Hervorhebung**: Ausgegraute nicht-editierbare Bereiche

### 3. Export & Speicherung

#### ✅ Autosave
- **Automatische Speicherung**: Alle 30 Sekunden
- **Zustandspersistierung**: Vollständiger Canvas-Zustand wird gespeichert
- **Fehlerbehandlung**: Robuste Fehlerbehandlung bei Speicherfehlern

#### ✅ Export-Funktionen
- **Format-Auswahl**: PNG oder PDF
- **Bereichsauswahl**: Gesamtes Canvas oder ausgewählte Bereiche
- **Export-Ziel**: Download oder automatische Ablage in "Dokumente"
- **Vorschau**: Export-Einstellungen werden vorab angezeigt

### 4. Benutzeroberfläche

#### ✅ Toolbar
- **Werkzeug-Auswahl**: Alle Objekttypen verfügbar
- **Status-Anzeige**: Aktive Nutzer und ausgewählte Objekte
- **Schnellaktionen**: Löschen, Export, Kollaboration

#### ✅ Responsive Design
- **Desktop-Optimiert**: Vollständige Funktionalität auf Desktop
- **Tablet-Support**: Touch-Gesten und optimierte Bedienung
- **Mobile-Anpassung**: Responsive Layout für verschiedene Bildschirmgrößen

#### ✅ Mehrsprachigkeit
- **Deutsch/Englisch**: Vollständige Übersetzung
- **Sprach-Umschaltung**: Dynamische Sprachänderung
- **Lokalisierung**: Alle Texte und Labels übersetzt

## Technische Architektur

### Backend (FastAPI + SQLAlchemy)

#### Datenbank-Modelle
```python
# Canvas-Haupttabelle
class Canvas(Base):
    id: int
    project_id: int
    name: str
    viewport_x/y/scale: float
    created_by: int

# Canvas-Objekte
class CanvasObject(Base):
    id: int
    object_id: str (UUID)
    canvas_id: int
    type: str (sticky, rectangle, circle, line, text, image)
    x, y, width, height, rotation: float
    content, color, font_size, font_family: str
    image_url: str
    points: JSON (für Linien)

# Kollaborationsbereiche
class CollaborationArea(Base):
    id: int
    area_id: str (UUID)
    canvas_id: int
    name: str
    x, y, width, height: float
    color: str
    assigned_users: JSON (Array von User-IDs)

# Canvas-Sessions (für Echtzeit-Kollaboration)
class CanvasSession(Base):
    id: int
    session_id: str (UUID)
    canvas_id: int
    user_id: int
    cursor_x/y: float
    is_active: bool
    joined_at, last_activity: datetime
```

#### API-Endpunkte
```python
# Canvas CRUD
GET    /api/v1/canvas/{project_id}     # Canvas laden/erstellen
PUT    /api/v1/canvas/{canvas_id}      # Canvas aktualisieren
DELETE /api/v1/canvas/{canvas_id}      # Canvas löschen

# Canvas State
POST   /api/v1/canvas/{canvas_id}/save # Zustand speichern
GET    /api/v1/canvas/{canvas_id}/load # Zustand laden

# Canvas Objects
POST   /api/v1/canvas/{canvas_id}/objects     # Objekt erstellen
PUT    /api/v1/canvas/objects/{object_id}     # Objekt aktualisieren
DELETE /api/v1/canvas/objects/{object_id}     # Objekt löschen

# Collaboration Areas
POST   /api/v1/canvas/{canvas_id}/areas       # Bereich erstellen
PUT    /api/v1/canvas/areas/{area_id}         # Bereich aktualisieren
DELETE /api/v1/canvas/areas/{area_id}         # Bereich löschen
POST   /api/v1/canvas/areas/{area_id}/assign/{user_id}  # Nutzer zuweisen
DELETE /api/v1/canvas/areas/{area_id}/assign/{user_id}  # Nutzer entfernen

# Active Users
GET    /api/v1/canvas/{canvas_id}/active-users # Aktive Nutzer

# Export
POST   /api/v1/canvas/{canvas_id}/export      # Canvas exportieren

# Statistics
GET    /api/v1/canvas/{canvas_id}/statistics  # Canvas-Statistiken

# WebSocket
WS     /api/v1/canvas/ws/{canvas_id}          # Echtzeit-Kollaboration
```

### Frontend (React + TypeScript)

#### Komponenten-Struktur
```
src/components/Canvas/
├── CanvasEditor.tsx          # Haupt-Editor-Komponente
├── CanvasToolbar.tsx         # Toolbar mit Werkzeugen
├── CanvasViewport.tsx        # Canvas-Viewport mit Pan/Zoom
├── CanvasObjectRenderer.tsx  # Objekt-Rendering
├── CollaborationPanel.tsx    # Kollaborations-Panel
└── ExportModal.tsx          # Export-Modal
```

#### State Management
```typescript
interface CanvasState {
  objects: CanvasObject[];
  areas: CollaborationArea[];
  viewport: { x: number; y: number; scale: number };
}

interface CanvasObject {
  id: string;
  type: 'sticky' | 'rectangle' | 'circle' | 'line' | 'text' | 'image';
  x, y, width, height, rotation: number;
  content, color: string;
  font_size, font_family?: string;
  image_url?: string;
}
```

#### WebSocket-Integration
```typescript
// WebSocket-Verbindung für Echtzeit-Kollaboration
const ws = new WebSocket(`ws://localhost:8000/api/v1/canvas/ws/${canvasId}`);

// Nachrichten-Typen
type CanvasMessage = 
  | { type: 'object_add'; data: CanvasObject }
  | { type: 'object_update'; data: { object_id: string; updates: any } }
  | { type: 'object_delete'; data: { object_id: string } }
  | { type: 'cursor_move'; data: { x: number; y: number } }
  | { type: 'user_join'; data: { user_id: number; user_name: string } }
  | { type: 'user_leave'; data: { user_id: number } };
```

## Installation & Setup

### 1. Backend-Setup
```bash
# Canvas-Tabellen erstellen
cd BuildWise
python create_canvas_tables.py

# Backend starten
uvicorn app.main:app --reload
```

### 2. Frontend-Setup
```bash
# Frontend starten
cd Frontend/Frontend
npm install
npm run dev
```

### 3. Abhängigkeiten
```bash
# Backend
pip install pillow  # Für Bild-Export

# Frontend
npm install react-hot-toast  # Für Toast-Benachrichtigungen
```

## Verwendung

### 1. Canvas öffnen
1. Projekt auswählen
2. Auf "Canvas" in der Dashboard-Navigation klicken
3. Canvas wird automatisch geladen oder erstellt

### 2. Objekte hinzufügen
1. Werkzeug in der Toolbar auswählen
2. Auf Canvas klicken um Objekt zu platzieren
3. Objekt kann sofort bearbeitet werden

### 3. Kollaboration
1. "Kollaboration"-Button klicken
2. Kollaborationsbereiche erstellen
3. Nutzer Bereichen zuweisen
4. Echtzeit-Zusammenarbeit starten

### 4. Export
1. "Export"-Button klicken
2. Format und Bereich wählen
3. Download oder Dokument-Speicherung wählen

## Performance-Optimierungen

### Backend
- **Asynchrone SQLAlchemy**: Optimierte Datenbankabfragen
- **WebSocket-Pooling**: Effiziente WebSocket-Verbindungen
- **Caching**: Canvas-Zustand-Caching für bessere Performance

### Frontend
- **React.memo**: Optimierte Komponenten-Rendering
- **useCallback/useMemo**: Vermeidung unnötiger Re-Renders
- **Virtual Scrolling**: Für große Canvas-Bereiche
- **Debounced Updates**: Reduzierung von API-Calls

## Sicherheit

### Authentifizierung
- **JWT-Token**: Alle API-Calls authentifiziert
- **Projekt-Zugriff**: Nur Projekt-Owner können Canvas bearbeiten
- **Session-Management**: Sichere WebSocket-Sessions

### Datenvalidierung
- **Pydantic-Schemas**: Strikte Datenvalidierung
- **SQL-Injection-Schutz**: Parameterisierte Queries
- **XSS-Schutz**: Eingabe-Sanitization

## Erweiterte Features

### Geplante Erweiterungen
- **Templates**: Vorgefertigte Canvas-Templates
- **Versionierung**: Canvas-Versionsverwaltung
- **Kommentare**: Objekt-Kommentare und Diskussionen
- **Integration**: Chat-Integration in Canvas
- **Mobile App**: Native Mobile-App

### API-Erweiterungen
- **Bulk-Operations**: Mehrere Objekte gleichzeitig bearbeiten
- **Webhook-Support**: Externe Integrationen
- **Plugin-System**: Erweiterbare Funktionalität

## Troubleshooting

### Häufige Probleme

#### Canvas lädt nicht
```bash
# Backend-Logs prüfen
tail -f logs/backend.log

# Datenbank-Verbindung testen
python -c "from app.core.database import engine; print('DB OK')"
```

#### WebSocket-Verbindung fehlschlägt
```bash
# WebSocket-Port prüfen
netstat -an | grep 8000

# CORS-Einstellungen prüfen
# .env-Datei: ALLOWED_ORIGINS=http://localhost:3000
```

#### Performance-Probleme
```bash
# Canvas-Größe reduzieren
# Weniger Objekte gleichzeitig anzeigen
# Browser-Cache leeren
```

## Fazit

Das Canvas-System wurde erfolgreich implementiert und bietet alle gewünschten MIRO-ähnlichen Funktionen:

✅ **Vollständige Canvas-Funktionalität** mit unendlichem Whiteboard  
✅ **Echtzeit-Kollaboration** mit WebSocket-Support  
✅ **Kollaborationsbereiche** mit Nutzerzuordnung  
✅ **Export-Funktionen** für Download und Dokument-Speicherung  
✅ **Responsive Design** für Desktop und Tablet  
✅ **Performance-optimiert** für große Canvas-Bereiche  
✅ **Sichere Architektur** mit Authentifizierung und Validierung  

Das System ist produktionsbereit und kann sofort verwendet werden. 