# BuildWise Environment Mode Switcher
## Elegante Beta/Production-Umschaltung

### 🎯 Problem-Lösung

**Problem:** 
- Umschaltung zwischen Beta (0.0% Gebühren) und Production (4.7% Gebühren) erforderte `.env`-Überschreibung
- OAuth-Credentials wurden dabei überschrieben
- Nicht robust und fehleranfällig

**Lösung:**
- Elegante Environment-Modus-Konfiguration über separate JSON-Datei
- Sichere Umschaltung ohne `.env`-Überschreibung
- Admin-Tools und API-Endpoints für einfache Verwaltung

### 🏗️ Architektur

#### Backend-Komponenten

1. **EnvironmentMode Enum** (`app/core/config.py`)
   ```python
   class EnvironmentMode(str, Enum):
       BETA = "beta"
       PRODUCTION = "production"
   ```

2. **Erweiterte Settings-Klasse**
   - `environment_mode`: Aktueller Modus
   - `buildwise_fee_percentage`: Automatisch basierend auf Modus
   - Methoden für Modus-Wechsel und Status-Abfrage

3. **API-Endpoints** (`app/api/environment_config.py`)
   - `GET /api/v1/environment/status` - Admin-Status
   - `POST /api/v1/environment/switch` - Modus-Wechsel
   - `GET /api/v1/environment/fee-config` - Gebühren-Konfiguration
   - `GET /api/v1/environment/info` - Öffentliche Informationen

4. **Admin-Tool** (`switch_environment_mode.py`)
   - Interaktives CLI-Tool
   - Kommandozeilen-Befehle
   - Sichere Konfigurationsverwaltung

#### Frontend-Komponenten

1. **EnvironmentService** (`Frontend/src/api/environmentService.ts`)
   - API-Client für Environment-Verwaltung
   - Typisierte Interfaces
   - Fehlerbehandlung

2. **EnvironmentManager** (`Frontend/src/components/EnvironmentManager.tsx`)
   - React-Komponente für UI
   - Admin- und Benutzer-Ansichten
   - Bestätigungs-Dialoge

### 🚀 Verwendung

#### 1. CLI-Tool (Empfohlen)

```bash
# Status anzeigen
python switch_environment_mode.py status

# Zu Beta wechseln
python switch_environment_mode.py beta

# Zu Production wechseln
python switch_environment_mode.py production

# Interaktives Menü
python switch_environment_mode.py interactive
```

#### 2. API-Endpoints

```bash
# Status abfragen (Admin)
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/environment/status

# Zu Beta wechseln (Admin)
curl -X POST -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"target_mode": "beta"}' \
     http://localhost:8000/api/v1/environment/switch

# Zu Production wechseln (Admin)
curl -X POST -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"target_mode": "production", "confirm": true}' \
     http://localhost:8000/api/v1/environment/switch

# Gebühren-Konfiguration (alle Benutzer)
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/environment/fee-config
```

#### 3. Frontend-Integration

```typescript
import { environmentService } from '../api/environmentService';

// Status abfragen
const status = await environmentService.getEnvironmentStatus();

// Modus wechseln
await environmentService.switchToBeta();
await environmentService.switchToProduction(true);

// Gebühren-Konfiguration
const config = await environmentService.getFeeConfiguration();
```

### 📊 Konfigurationsdatei

Die Konfiguration wird in `environment_config.json` gespeichert:

```json
{
  "environment_mode": "beta",
  "last_switch": "2024-01-15T10:30:00",
  "fee_percentage": 0.0
}
```

### 🔒 Sicherheit

- **Admin-Berechtigung**: Nur Administratoren können Modus wechseln
- **Bestätigung**: Production-Wechsel erfordert explizite Bestätigung
- **Audit-Trail**: Letzter Wechsel wird protokolliert
- **Validierung**: Ungültige Modi werden abgelehnt

### 🎯 Modus-Verhalten

#### Beta-Modus
- **Gebühren**: 0.0%
- **Zweck**: Test- und Entwicklungsphase
- **Features**: Vollständige Funktionalität ohne Gebühren

#### Production-Modus
- **Gebühren**: 4.7%
- **Zweck**: Live-Betrieb
- **Features**: Vollständige Funktionalität mit Gebühren

### 🔧 Integration in bestehende Services

Die `BuildWiseFeeService` verwendet automatisch die neue Konfiguration:

```python
# In app/services/buildwise_fee_service.py
fee_percentage = settings.get_current_fee_percentage()
```

### 📱 Frontend-Integration

Die `EnvironmentManager`-Komponente kann in bestehende Seiten integriert werden:

```tsx
import EnvironmentManager from '../components/EnvironmentManager';

// In einer Admin-Seite
<EnvironmentManager isAdmin={true} onEnvironmentChange={handleChange} />

// In einer Benutzer-Seite
<EnvironmentManager isAdmin={false} />
```

### 🛠️ Wartung

#### Konfiguration zurücksetzen
```bash
# Konfigurationsdatei löschen
rm environment_config.json

# System startet automatisch im Beta-Modus
```

#### Logs prüfen
```bash
# Backend-Logs
tail -f logs/buildwise.log

# Environment-Wechsel protokollieren
grep "environment" logs/buildwise.log
```

### 🎉 Vorteile der neuen Lösung

1. **Sicherheit**: Keine `.env`-Überschreibung mehr
2. **Robustheit**: Separate Konfigurationsdatei
3. **Benutzerfreundlichkeit**: Einfache CLI- und UI-Tools
4. **Skalierbarkeit**: API-Endpoints für Automatisierung
5. **Audit**: Protokollierung aller Wechsel
6. **Validierung**: Sichere Modus-Validierung
7. **Integration**: Nahtlose Integration in bestehende Services

### 🔮 Zukünftige Erweiterungen

- **Zeitgesteuerte Wechsel**: Automatische Umschaltung zu bestimmten Zeiten
- **A/B-Testing**: Verschiedene Gebühren-Sätze testen
- **Rollback-Funktion**: Automatisches Zurücksetzen bei Problemen
- **Monitoring**: Dashboard für Environment-Metriken
- **Webhooks**: Benachrichtigungen bei Modus-Wechseln

### 📞 Support

Bei Fragen oder Problemen:
1. CLI-Tool mit `--help` ausführen
2. API-Dokumentation unter `/docs` prüfen
3. Logs für Fehlerdetails analysieren
4. Konfigurationsdatei auf Konsistenz prüfen 