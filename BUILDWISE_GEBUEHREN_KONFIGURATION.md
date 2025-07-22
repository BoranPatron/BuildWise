# BuildWise Gebühren-Konfiguration

## Übersicht

Das BuildWise-Gebühren-System ermöglicht eine flexible Konfiguration der Plattform-Gebühren für verschiedene Phasen der Plattform-Entwicklung.

## Phasen

### 1. Beta-Phase (0% Gebühr)
- **Zweck**: Kostenlose Nutzung für Beta-Tester
- **Gebühr**: 0%
- **Zielgruppe**: Ausgewählte Beta-Tester
- **Dauer**: Bis zum Go-Live

### 2. Go-Live (4% Gebühr)
- **Zweck**: Kommerzielle Nutzung
- **Gebühr**: 4%
- **Zielgruppe**: Alle Nutzer
- **Dauer**: Ab Go-Live

## Konfiguration

### Umgebungsvariablen

Die Gebühren-Konfiguration erfolgt über Umgebungsvariablen:

```bash
# Gebühren-Konfiguration
BUILDWISE_FEE_PERCENTAGE=0.0          # 0% für Beta, 4.0 für Go-Live
BUILDWISE_FEE_PHASE=beta              # "beta" oder "production"
BUILDWISE_FEE_ENABLED=true            # true/false
```

### Standard-Konfiguration

```python
# app/core/config.py
buildwise_fee_percentage: float = 0.0  # 0% für Beta-Phase, 4.0 für Go-Live
buildwise_fee_phase: str = "beta"      # "beta" oder "production"
buildwise_fee_enabled: bool = True     # Aktiviert/Deaktiviert die Gebühren-Berechnung
```

## Admin-Tool

### Verwendung

```bash
# Aktuellen Status anzeigen
python switch_buildwise_fees.py --status

# Zu Beta-Phase wechseln (0%)
python switch_buildwise_fees.py --phase beta

# Zu Go-Live wechseln (4%)
python switch_buildwise_fees.py --phase production

# Gebühren deaktivieren
python switch_buildwise_fees.py --disable

# Gebühren aktivieren
python switch_buildwise_fees.py --enable

# Statistiken anzeigen
python switch_buildwise_fees.py --stats

# .env-Datei erstellen
python switch_buildwise_fees.py --create-env
```

### Beispiel-Ausgabe

```
🔧 BuildWise Gebühren-Konfiguration
==================================================
📊 Aktueller Prozentsatz: 0.0%
🏷️  Aktuelle Phase: beta
✅ Aktiviert: Ja
📝 Beschreibung: Beta-Phase (kostenlos für Beta-Tester)

💡 Verfügbare Phasen:
  ✓ beta: 0.0% - Beta-Phase (kostenlos für Beta-Tester)
    production: 4.0% - Go-Live (4% Gebühr für alle Nutzer)
```

## API-Endpunkte

### Konfiguration abrufen
```http
GET /api/v1/buildwise-fees/config
```

**Response:**
```json
{
  "fee_percentage": 0.0,
  "fee_phase": "beta",
  "fee_enabled": true
}
```

### Konfiguration aktualisieren (Admin only)
```http
PUT /api/v1/buildwise-fees/config
Content-Type: application/json

{
  "fee_percentage": 4.0,
  "fee_phase": "production",
  "fee_enabled": true
}
```

## Service-Methoden

### BuildWiseFeeService

```python
# Aktuelle Konfiguration abrufen
percentage = BuildWiseFeeService.get_current_fee_percentage()
phase = BuildWiseFeeService.get_current_fee_phase()
enabled = BuildWiseFeeService.is_fee_enabled()

# Gebühr erstellen (verwendet automatisch aktuelle Konfiguration)
fee = await BuildWiseFeeService.create_fee_from_quote(
    db=db,
    quote_id=quote_id,
    cost_position_id=cost_position_id
)
```

## Implementierung

### 1. Konfiguration (app/core/config.py)
- Neue Umgebungsvariablen für Gebühren-Konfiguration
- Standardwerte für Beta-Phase

### 2. Service (app/services/buildwise_fee_service.py)
- Neue Methoden für Konfigurationsabfrage
- Automatische Verwendung der konfigurierten Werte
- Validierung der Gebühren-Aktivierung

### 3. API (app/api/buildwise_fee.py)
- Neue Endpunkte für Konfigurationsverwaltung
- Admin-Berechtigungen für Konfigurationsänderungen
- Validierung der Eingabewerte

### 4. Schemas (app/schemas/buildwise_fee.py)
- Neue Response-Schemas für Konfiguration
- Validierung der Konfigurationswerte

### 5. Admin-Tool (switch_buildwise_fees.py)
- Kommandozeilen-Tool für einfache Umschaltung
- Status-Anzeige und Statistiken
- Bestätigungsdialoge für kritische Änderungen

## Sicherheit

### Admin-Berechtigungen
- Nur Administratoren können die Gebühren-Konfiguration ändern
- API-Endpunkte prüfen Admin-Status
- Tool erfordert manuelle Bestätigung

### Validierung
- Prozentsatz muss zwischen 0 und 100 liegen
- Phase muss "beta" oder "production" sein
- Gebühren können komplett deaktiviert werden

## Migration von bestehenden Gebühren

### Automatische Anpassung
- Bestehende Gebühren bleiben unverändert
- Neue Gebühren verwenden aktuelle Konfiguration
- Keine Rückwirkung auf bereits erstellte Gebühren

### Manuelle Anpassung (falls benötigt)
```sql
-- Alle bestehenden Gebühren auf 0% setzen (Beta-Phase)
UPDATE buildwise_fees 
SET fee_percentage = 0.0, 
    fee_details = CONCAT(fee_details, ' (Beta-Phase)')
WHERE fee_percentage > 0;
```

## Monitoring

### Logs
- Alle Konfigurationsänderungen werden geloggt
- Gebühren-Erstellung mit Phase-Information
- Fehler bei deaktivierten Gebühren

### Statistiken
- Separate Statistiken für Beta- und Production-Phase
- Tracking der Umschaltungen
- Monitoring der Gebühren-Einnahmen

## Best Practices

### 1. Vor Go-Live
```bash
# Testen der Production-Konfiguration
python switch_buildwise_fees.py --phase production
python switch_buildwise_fees.py --status
```

### 2. Go-Live
```bash
# Umschaltung zu Production
python switch_buildwise_fees.py --phase production
```

### 3. Monitoring
```bash
# Regelmäßige Status-Prüfung
python switch_buildwise_fees.py --status
python switch_buildwise_fees.py --stats
```

### 4. Rollback (falls benötigt)
```bash
# Zurück zu Beta-Phase
python switch_buildwise_fees.py --phase beta
```

## Troubleshooting

### Gebühren werden nicht erstellt
1. Prüfen Sie ob Gebühren aktiviert sind: `python switch_buildwise_fees.py --status`
2. Prüfen Sie die Logs auf Fehlermeldungen
3. Stellen Sie sicher, dass der Service neu gestartet wurde

### Falsche Gebühren-Höhe
1. Prüfen Sie die aktuelle Konfiguration: `python switch_buildwise_fees.py --status`
2. Stellen Sie sicher, dass die .env-Datei korrekt geladen wird
3. Restarten Sie den Service nach Konfigurationsänderungen

### Admin-Berechtigungen
1. Stellen Sie sicher, dass der Benutzer Admin-Rechte hat
2. Prüfen Sie die JWT-Token-Berechtigungen
3. Verwenden Sie das Admin-Tool für direkte Änderungen

## Zukünftige Erweiterungen

### Geplante Features
- Zeitbasierte automatische Umschaltung
- Benutzer-spezifische Gebühren-Sätze
- Erweiterte Statistiken und Reporting
- Web-Interface für Konfigurationsverwaltung

### Skalierbarkeit
- Unterstützung für weitere Phasen
- Dynamische Gebühren-Sätze
- A/B-Testing für Gebühren-Modelle 