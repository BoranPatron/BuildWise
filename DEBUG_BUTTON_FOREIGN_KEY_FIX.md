# Debug-Button Foreign Key Constraint Fix

## Problem

Der Debug-Button "Alle Datenbankeinträge löschen" führte zu einem Foreign Key Constraint Fehler:

```
IntegrityError: update or delete on table "quotes" violates foreign key constraint "cost_positions_quote_id_fkey" on table "cost_positions"
```

## Ursache

Die ursprüngliche Löschreihenfolge war nicht korrekt und respektierte die Foreign Key Constraints nicht:

**Falsche Reihenfolge:**
1. `quotes` (wurde vor `cost_positions` gelöscht)
2. `cost_positions` (verweist auf `quotes` → Fehler!)

## Lösung

Die Löschreihenfolge wurde korrigiert, um die Foreign Key Dependencies zu respektieren:

**Korrekte Reihenfolge:**
1. `buildwise_fee_items` (abhängig von `buildwise_fees`)
2. `buildwise_fees` (abhängig von `quotes`)
3. `cost_positions` (abhängig von `quotes` und `milestones`)
4. `quotes` (abhängig von `milestones` und `service_providers`)
5. `expenses` (unabhängig)
6. `documents` (unabhängig)
7. `messages` (unabhängig)
8. `tasks` (unabhängig)
9. `milestones` (zuletzt, da andere davon abhängen)

## Implementierte Änderungen

### Datei: `app/api/milestones.py`

**Vorher:**
```python
# 3. Angebote löschen (abhängig von Milestone und ServiceProvider)
await db.execute(Quote.__table__.delete())

# 8. Kostenpositionen löschen (abhängig von Milestone)
await db.execute(CostPosition.__table__.delete())
```

**Nachher:**
```python
# 3. Kostenpositionen löschen (abhängig von Quote und Milestone)
await db.execute(CostPosition.__table__.delete())

# 4. Angebote löschen (abhängig von Milestone und ServiceProvider)
await db.execute(Quote.__table__.delete())
```

## Datenbank-Beziehungen

### Foreign Key Dependencies

```
buildwise_fee_items → buildwise_fees
buildwise_fees → quotes
cost_positions → quotes, milestones
quotes → milestones, users (service_providers)
tasks → milestones (optional)
documents → users (uploader)
messages → users (sender, recipient)
expenses → projects
```

### Wichtige Constraints

1. **BuildWiseFee → Quote**: `buildwise_fees.quote_id` → `quotes.id`
2. **BuildWiseFeeItem → BuildWiseFee**: `buildwise_fee_items.buildwise_fee_id` → `buildwise_fees.id`
3. **CostPosition → Quote**: `cost_positions.quote_id` → `quotes.id`
4. **CostPosition → Milestone**: `cost_positions.milestone_id` → `milestones.id`
5. **Quote → Milestone**: `quotes.milestone_id` → `milestones.id`

## Vorteile der Korrektur

### 1. Datenintegrität
- Foreign Key Constraints werden respektiert
- Keine verwaisten Referenzen
- Konsistente Datenbankstruktur

### 2. Zuverlässigkeit
- Debug-Button funktioniert zuverlässig
- Keine Fehler beim Löschen
- Saubere Entwicklungsumgebung

### 3. Wartbarkeit
- Klare Abhängigkeitsstruktur
- Dokumentierte Löschreihenfolge
- Einfache Erweiterung bei neuen Tabellen

## Testing

### Manueller Test
1. Debug-Button in der Bauträgeransicht klicken
2. Bestätigung geben
3. Überprüfen, dass alle Daten gelöscht wurden
4. Keine Foreign Key Fehler

### Automatisierter Test
```python
def test_debug_delete_all_endpoint():
    # Setup: Daten in allen Tabellen erstellen
    # ...
    
    # Execute: Debug-Button Endpoint aufrufen
    response = client.delete("/milestones/debug/delete-all-milestones-and-quotes")
    
    # Assert: Keine Fehler, alle Daten gelöscht
    assert response.status_code == 200
    # Überprüfen, dass alle Tabellen leer sind
```

## Best Practices für zukünftige Änderungen

### 1. Neue Tabellen hinzufügen
- Foreign Key Dependencies dokumentieren
- Löschreihenfolge entsprechend anpassen
- Tests für Debug-Button erweitern

### 2. Constraints ändern
- Auswirkungen auf Löschreihenfolge prüfen
- Debug-Button Test aktualisieren
- Dokumentation erweitern

### 3. Entwicklung
- Immer Foreign Key Dependencies berücksichtigen
- Löschreihenfolge bei Änderungen anpassen
- Tests für Debug-Funktionalität schreiben

## Fazit

Die Korrektur der Löschreihenfolge im Debug-Button stellt sicher, dass alle Foreign Key Constraints respektiert werden. Dies ermöglicht eine zuverlässige und sichere Entwicklungsumgebung ohne Datenintegritätsprobleme. 