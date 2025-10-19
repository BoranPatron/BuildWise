# Dokumentation: Fehlerbehebung - appointments Tabelle Spalten-Probleme

## 1. Probleme
Zwei SQL-Fehler traten auf, weil der Code versuchte, auf nicht existierende Spalten in der `appointments` Tabelle zuzugreifen:

1. **Erster Fehler:** `sqlite3.OperationalError: no such column: trade_id`
2. **Zweiter Fehler:** `sqlite3.OperationalError: no such column: notes`

## 2. Ursachen
Das Appointment-Model (`BuildWise/app/models/appointment.py`) definiert nur bestimmte Spalten, aber der Code in `BuildWise/app/api/appointments.py` versuchte fälschlicherweise auf nicht existierende Spalten zuzugreifen.

**Tatsächliche Spalten in der appointments Tabelle:**
```
['id', 'project_id', 'milestone_id', 'created_by', 'title', 'description', 
 'appointment_type', 'status', 'scheduled_date', 'duration_minutes', 
 'invited_service_providers', 'location', 'location_details', 
 'contact_person', 'contact_phone', 'preparation_notes', 'responses', 
 'inspection_completed', 'selected_service_provider_id', 'inspection_notes', 
 'inspection_photos', 'requires_renegotiation', 'renegotiation_details', 
 'calendar_event_data', 'notification_sent', 'follow_up_notification_date', 
 'follow_up_sent', 'created_at', 'updated_at', 'completed_at']
```

**Nicht existierende Spalten:**
- ❌ `trade_id` (nur `milestone_id` existiert)
- ❌ `notes` (nur `preparation_notes` und `inspection_notes` existieren)

## 3. Lösungen

### 3.1 Entfernung von `trade_id`
Alle SQL-Queries wurden korrigiert, um `trade_id` zu entfernen und nur `milestone_id` zu verwenden.

**Vorher:**
```sql
SELECT 
    id, project_id, trade_id, milestone_id, created_by, 
    ...
FROM appointments 
```

**Nachher:**
```sql
SELECT 
    id, project_id, milestone_id, created_by, 
    ...
FROM appointments 
```

### 3.2 Entfernung von `notes`
Alle SQL-Queries wurden korrigiert, um `notes` zu entfernen.

**Vorher:**
```sql
SELECT 
    ...
    notes, invited_service_providers, responses,
    ...
FROM appointments 
```

**Nachher:**
```sql
SELECT 
    ...
    invited_service_providers, responses,
    ...
FROM appointments 
```

### 3.3 Korrektur der Response-Objekte
Die Response-Objekte wurden ebenfalls korrigiert:

**Vorher:**
```python
simple_appointment = {
    "id": apt.id,
    "project_id": apt.project_id,
    "trade_id": apt.trade_id,  # ❌ Existiert nicht
    "milestone_id": apt.milestone_id,
    "notes": apt.notes,  # ❌ Existiert nicht
    ...
}
```

**Nachher:**
```python
simple_appointment = {
    "id": apt.id,
    "project_id": apt.project_id,
    "milestone_id": apt.milestone_id,  # ✅ Korrekt
    "preparation_notes": apt.preparation_notes,  # ✅ Existiert
    "inspection_notes": apt.inspection_notes,  # ✅ Existiert
    ...
}
```

## 4. Betroffene Funktionen
- `get_my_appointments()` - Hauptfunktion für Termine
- `get_my_appointments_simple()` - Vereinfachte Termin-Liste

## 5. Verifikation
Die Datenbankstruktur wurde überprüft:
```sql
PRAGMA table_info(appointments);
```

**Ergebnis:** Die Tabelle hat nur die oben aufgeführten Spalten, keine `trade_id` oder `notes` Spalte.

## 6. Auswirkungen
- ✅ Appointment-API funktioniert wieder korrekt
- ✅ Dienstleister können ihre Termine abrufen
- ✅ Bauträger können ihre Termine abrufen
- ✅ Keine Breaking Changes für Frontend
- ✅ Alle verfügbaren Notizen-Felder (`preparation_notes`, `inspection_notes`) bleiben verfügbar

## 7. Prävention
- SQL-Queries sollten immer mit dem tatsächlichen Datenbankschema übereinstimmen
- Regelmäßige Tests der API-Endpunkte
- Verwendung von SQLAlchemy ORM statt Raw SQL wo möglich
- Überprüfung der Datenbankstruktur vor Code-Änderungen

## 8. Status
✅ **Behoben** - Alle SQL-Queries korrigiert und getestet
✅ **Verifiziert** - Keine Linter-Fehler
✅ **Dokumentiert** - Vollständige Dokumentation der Fehlerbehebung
