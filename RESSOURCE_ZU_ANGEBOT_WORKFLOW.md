# Ressource-zu-Angebot Workflow - Implementierungsplan

## Übersicht
Wenn ein Bauträger eine Ressource einer Ausschreibung zuordnet, muss der Dienstleister aufgefordert werden, ein Angebot abzugeben oder abzulehnen.

## Workflow

1. **Bauträger ordnet Ressource zu** → ResourceAllocation wird erstellt mit `allocation_status = 'pre_selected'`
2. **System sendet Benachrichtigung** → Dienstleister erhält Benachrichtigung über Ressourcenverwaltung
3. **Dienstleister reagiert**:
   - **Angebot abgeben** → Quote wird erstellt, ResourceAllocation Status → `offer_submitted`
   - **Ablehnen** → ResourceAllocation Status → `rejected`
4. **Nach Angebotserstellung** → Ressource wird aus "Zugeordnete Ressourcen" entfernt

## Datenbank-Schema

### Resource Status (erweitert)
- `available` - Verfügbar
- `allocated` - Angezogen/zugeordnet  
- `quote_submitted` - Angebot wurde abgegeben
- `rejected` - Abgelehnt
- `completed` - Abgeschlossen

### ResourceAllocation Status
- `pre_selected` - Vorausgewählt (wartet auf Angebot)
- `offer_submitted` - Angebot wurde eingereicht
- `accepted` - Angebot angenommen
- `rejected` - Abgelehnt
- `completed` - Abgeschlossen

## API-Endpunkte (neu)

### 1. POST /api/v1/resources/allocations/{allocation_id}/submit-quote
```python
{
  "quote_data": {
    "title": "string",
    "total_amount": number,
    "labor_cost": number,
    "material_cost": number,
    "description": "string",
    ...
  }
}
```
**Response**: Erstellt Quote und aktualisiert ResourceAllocation

### 2. POST /api/v1/resources/allocations/{allocation_id}/reject
```python
{
  "rejection_reason": "string"
}
```
**Response**: Setzt ResourceAllocation auf rejected

### 3. GET /api/v1/resources/allocations/my-pending
**Response**: Liste aller Allocations die auf Angebot/Ablehnung warten

## Benachrichtigungssystem

### Neue Benachrichtigung bei Ressourcen-Zuordnung
- **Typ**: `RESOURCE_ALLOCATED`
- **Priorität**: `HIGH`
- **Titel**: "Ressource einer Ausschreibung zugeordnet"
- **Nachricht**: Details mit Projekt, Gewerk, Zeitraum
- **Action-Button**: "Zur Ressourcenverwaltung" → `/resources`

### Benachrichtigungs-Daten
```json
{
  "allocation_id": 123,
  "resource_id": 456,
  "trade_id": 789,
  "trade_title": "Elektroinstallation",
  "project_name": "Neubau Musterstraße",
  "bautraeger_name": "Mustermann GmbH",
  "allocated_start_date": "2025-01-15",
  "allocated_end_date": "2025-02-28",
  "allocated_person_count": 3,
  "action_required": true
}
```

## Frontend-Komponenten

### ResourceManagementDashboard (erweitert)
- Angezogene Ressourcen mit "Aktion erforderlich" Badge
- Button "Angebot abgeben" / "Ablehnen"
- Modal für Angebotserstellung
- Statusanzeige für eingereichte Angebote

### NotificationTab (erweitert)
- Spezielle Darstellung für RESOURCE_ALLOCATED
- Button "Zur Ressourcenverwaltung"
- Badge für Anzahl wartender Aktionen

## Implementierungs-Reihenfolge

1. ✅ Notification Service erweitern (bereits vorhanden)
2. Backend: API-Endpunkte für submit-quote und reject
3. Backend: Status-Update-Logik
4. Frontend: ResourceManagementDashboard erweitern
5. Frontend: NotificationTab erweitern
6. Frontend: TradeDetailsModal Filter für Ressourcen
7. Testing: End-to-End Workflow

## Best Practices

1. **Transaktionale Konsistenz**: Quote-Erstellung und Status-Update in einer Transaktion
2. **Fehlerbehandlung**: Rollback bei Fehlern, klare Error Messages
3. **Validierung**: Prüfung ob Allocation noch pending ist
4. **Benachrichtigungen**: Async-Processing für Benachrichtigungen
5. **Status-Tracking**: Audit-Log für Status-Änderungen
6. **UI/UX**: Klare Kennzeichnung, eindeutige Call-to-Actions

