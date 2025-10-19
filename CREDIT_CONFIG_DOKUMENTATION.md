# BuildWise Credit-Konfiguration

## Übersicht

Das BuildWise Credit-System wurde erweitert um ein globales Konfigurationssystem, das es ermöglicht, Credit-Belohnungen und System-Parameter zur Laufzeit anzupassen, ohne den Code neu kompilieren zu müssen.

## Neue Dateien

### `app/config/credit_config.py`
Das zentrale Konfigurationsmodul enthält:
- **Credit-Rewards**: Belohnungen für verschiedene Aktionen
- **System-Parameter**: Tägliche Abzüge, Warnschwellen, etc.
- **Feature-Flags**: Aktivierung/Deaktivierung von Features
- **Credit-Packages**: Konfiguration der verfügbaren Pakete
- **Helper-Methoden**: Für einfache Verwaltung der Konfiguration

### `app/config/__init__.py`
Exportiert die wichtigsten Konfigurationsklassen für einfache Imports.

## Anpassungen an bestehenden Dateien

### `app/services/credit_service.py`
- Import des neuen Konfigurationsmoduls
- Entfernung der hardcodierten `CREDIT_REWARDS`
- Verwendung der Konfiguration für alle Credit-Berechnungen
- Neue Methoden für Konfigurationsverwaltung:
  - `update_credit_config()`: Aktualisiert Konfiguration zur Laufzeit
  - `get_credit_config()`: Holt aktuelle Konfiguration
  - `validate_credit_config()`: Validiert Konfiguration

### `app/api/credits.py`
- Neue Admin-Endpunkte für Konfigurationsverwaltung:
  - `GET /credits/admin/config`: Holt aktuelle Konfiguration
  - `POST /credits/admin/config/update`: Aktualisiert einen Wert
  - `POST /credits/admin/config/validate`: Validiert Konfiguration
  - `POST /credits/admin/config/reset`: Setzt auf Standardwerte zurück

## Verwendung

### 1. Konfiguration anpassen

#### Über die API (Empfohlen für Produktion):
```bash
# Credit-Belohnung für Angebot annehmen von 5 auf 7 Credits erhöhen
curl -X POST "http://localhost:8000/api/credits/admin/config/update" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event_type": "quote_accepted", "new_amount": 7}'
```

#### Direkt im Code (Für Entwicklung):
```python
from app.config.credit_config import credit_config

# Credit-Belohnung ändern
credit_config.update_credit_reward(CreditEventType.QUOTE_ACCEPTED, 7)

# Feature aktivieren/deaktivieren
credit_config.toggle_feature('enable_inspection_bonus', True)
```

### 2. Aktuelle Konfiguration abrufen

```python
from app.config.credit_config import credit_config

# Alle Konfigurationswerte
config = credit_config.get_all_config()

# Spezifische Belohnung
reward = credit_config.get_credit_reward(CreditEventType.QUOTE_ACCEPTED)

# Feature-Status prüfen
is_enabled = credit_config.is_feature_enabled('enable_inspection_bonus')
```

### 3. Konfiguration validieren

```python
from app.config.credit_config import validate_credit_config

if validate_credit_config():
    print("Konfiguration ist gültig!")
else:
    print("Konfiguration hat Fehler!")
```

## Verfügbare Event-Typen

| Event-Typ | Standard-Belohnung | Beschreibung |
|-----------|-------------------|--------------|
| `QUOTE_ACCEPTED` | 5 Credits | Angebot angenommen |
| `INSPECTION_QUOTE_ACCEPTED` | 15 Credits | Angebot nach Besichtigung angenommen (Bonus!) |
| `INVOICE_RECEIVED` | 3 Credits | Rechnung erhalten |
| `PROJECT_COMPLETED` | 10 Credits | Projekt abgeschlossen |
| `PROVIDER_REVIEW` | 2 Credits | Dienstleister bewertet |
| `MILESTONE_COMPLETED` | 3 Credits | Meilenstein abgeschlossen |
| `DOCUMENT_UPLOADED` | 1 Credit | Dokument hochgeladen |
| `EXPENSE_ADDED` | 1 Credit | Ausgabe hinzugefügt |
| `REGISTRATION_BONUS` | 90 Credits | Registrierungs-Bonus (Willkommensbonus) |
| `REFERRAL_BONUS` | 20 Credits | Empfehlungs-Bonus |
| `LOYALTY_BONUS` | 10 Credits | Treue-Bonus |

## System-Parameter

| Parameter | Standard-Wert | Beschreibung |
|-----------|---------------|--------------|
| `DAILY_CREDIT_DEDUCTION` | 1 | Täglicher Credit-Abzug für Pro-Status |
| `LOW_CREDIT_WARNING_THRESHOLD` | 10 | Warnung bei niedrigen Credits |
| `MIN_CREDITS_FOR_PRO` | 1 | Mindest-Credits für Pro-Status |
| `INSPECTION_BONUS_MULTIPLIER` | 3.0 | Multiplikator für Besichtigungs-Bonus |
| `MAX_CREDITS_PER_DAY` | 100 | Maximale Credits pro Tag (Anti-Spam) |

## Feature-Flags

| Feature | Standard | Beschreibung |
|---------|----------|--------------|
| `enable_inspection_bonus` | ✅ | Besichtigungs-Bonus aktiviert |
| `enable_loyalty_bonus` | ✅ | Treue-Bonus aktiviert |
| `enable_referral_bonus` | ✅ | Empfehlungs-Bonus aktiviert |
| `enable_daily_deduction` | ✅ | Täglicher Abzug aktiviert |
| `enable_auto_upgrade` | ✅ | Automatisches Upgrade aktiviert |
| `enable_auto_downgrade` | ✅ | Automatisches Downgrade aktiviert |

## API-Endpunkte

### Admin-Endpunkte (nur für ADMIN-Rolle)

#### Konfiguration abrufen
```http
GET /api/credits/admin/config
Authorization: Bearer YOUR_ADMIN_TOKEN
```

#### Konfiguration aktualisieren
```http
POST /api/credits/admin/config/update
Authorization: Bearer YOUR_ADMIN_TOKEN
Content-Type: application/json

{
  "event_type": "quote_accepted",
  "new_amount": 7
}
```

#### Konfiguration validieren
```http
POST /api/credits/admin/config/validate
Authorization: Bearer YOUR_ADMIN_TOKEN
```

#### Konfiguration zurücksetzen
```http
POST /api/credits/admin/config/reset
Authorization: Bearer YOUR_ADMIN_TOKEN
```

## Vorteile der neuen Konfiguration

1. **Flexibilität**: Credit-Belohnungen können zur Laufzeit angepasst werden
2. **Keine Downtime**: Änderungen erfordern keinen Neustart der Anwendung
3. **Zentrale Verwaltung**: Alle Konfigurationen an einem Ort
4. **Validierung**: Automatische Überprüfung der Konfiguration
5. **Audit-Trail**: Alle Änderungen werden protokolliert
6. **Feature-Flags**: Einfache Aktivierung/Deaktivierung von Features
7. **Anti-Spam**: Konfigurierbare Limits pro Tag/Aktion

## Migration von der alten Implementierung

Die alte hardcodierte `CREDIT_REWARDS` Dictionary wurde durch das neue Konfigurationssystem ersetzt. Alle bestehenden Funktionalitäten bleiben erhalten, aber jetzt konfigurierbar.

### Vorher:
```python
CREDIT_REWARDS = {
    CreditEventType.QUOTE_ACCEPTED: 5,
    # ...
}
```

### Nachher:
```python
from app.config.credit_config import credit_config

reward = credit_config.get_credit_reward(CreditEventType.QUOTE_ACCEPTED)
```

## Sicherheit

- Alle Konfigurationsänderungen erfordern ADMIN-Berechtigung
- Alle Änderungen werden im Audit-Log protokolliert
- Validierung verhindert ungültige Konfigurationen
- Anti-Spam-Limits verhindern Missbrauch

## Monitoring

Die Konfiguration kann über die API-Endpunkte überwacht werden:
- Aktuelle Werte abrufen
- Validierung durchführen
- Änderungshistorie im Audit-Log einsehen

## Beispiele für häufige Anpassungen

### 1. Besichtigungs-Bonus erhöhen
```bash
curl -X POST "http://localhost:8000/api/credits/admin/config/update" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event_type": "inspection_quote_accepted", "new_amount": 20}'
```

### 2. Täglichen Abzug reduzieren
```python
credit_config.DAILY_CREDIT_DEDUCTION = 0.5  # Nur halber Credit pro Tag
```

### 3. Feature temporär deaktivieren
```python
credit_config.toggle_feature('enable_daily_deduction', False)
```

### 4. Warnschwelle anpassen
```python
credit_config.LOW_CREDIT_WARNING_THRESHOLD = 20  # Warnung bei 20 Credits
```

## Troubleshooting

### Konfiguration ist ungültig
1. Führe Validierung aus: `POST /api/credits/admin/config/validate`
2. Prüfe die Logs auf spezifische Fehler
3. Setze auf Standardwerte zurück: `POST /api/credits/admin/config/reset`

### Änderungen werden nicht wirksam
1. Prüfe ob der User ADMIN-Berechtigung hat
2. Validiere die Konfiguration
3. Prüfe die Logs auf Fehler

### Performance-Probleme
1. Prüfe die Anti-Spam-Limits
2. Validiere die Konfiguration
3. Überwache die Audit-Logs auf häufige Änderungen
