# BuildWise Gebühren - Implementierungsdokumentation

## Übersicht

Die BuildWise-Gebühren (Vermittlungsgebühren) werden automatisch erstellt, wenn ein Bauträger ein Angebot eines Dienstleisters annimmt. Die Gebühr beträgt **4.7%** des Angebotsbetrags und ist **30 Tage nach Erstellung** fällig.

## Workflow

### 1. Angebot wird akzeptiert

Wenn ein Bauträger ein Angebot annimmt:

```
Bauträger akzeptiert Angebot
    ↓
Kostenposition wird erstellt (erscheint in "Finanzen" auf Startseite)
    ↓
BuildWise-Gebühr wird automatisch erstellt
    ↓
Gebühr erscheint in /buildwise-fees für Dienstleister
```

### 2. Automatische Berechnung

**Beispiel:**
- Angebotsbetrag: €10,000
- Provisionssatz: 4.7%
- Nettobetrag Gebühr: €470.00
- MwSt. (19%): €89.30
- Bruttobetrag Gebühr: €559.30
- Fälligkeitsdatum: +30 Tage ab heute

## Technische Implementierung

### Datenbankmodell

**Tabelle:** `buildwise_fees`

Wichtigste Felder:
- `project_id` - Referenz zum Projekt
- `quote_id` - Referenz zum akzeptierten Angebot
- `cost_position_id` - Referenz zur Kostenposition
- `service_provider_id` - Dienstleister, der die Gebühr zahlen muss
- `fee_amount` - Nettobetrag der Gebühr
- `fee_percentage` - Provisionssatz (4.7%)
- `quote_amount` - Ursprünglicher Angebotsbetrag
- `invoice_number` - Format: BW-XXXXXX
- `invoice_date` - Rechnungsdatum
- `due_date` - Fälligkeitsdatum (+30 Tage)
- `status` - Status: 'open', 'paid', 'overdue', 'cancelled'
- `tax_rate` - MwSt.-Satz (19%)
- `tax_amount` - MwSt.-Betrag
- `net_amount` - Nettobetrag
- `gross_amount` - Bruttobetrag

### Service-Layer

**Datei:** `app/services/buildwise_fee_service.py`

#### Hauptmethode: `create_fee_from_quote()`

```python
async def create_fee_from_quote(
    db: AsyncSession, 
    quote_id: int, 
    cost_position_id: int, 
    fee_percentage: Optional[float] = None
) -> BuildWiseFee
```

**Funktionsweise:**
1. Validiert, dass das Angebot existiert und akzeptiert wurde
2. Prüft, ob bereits eine Gebühr für dieses Angebot existiert
3. Verwendet Provisionssatz aus Konfiguration (4.7% in Production, 0% in Beta)
4. Berechnet Gebührenbetrag: `quote_amount * (fee_percentage / 100)`
5. Generiert eindeutige Rechnungsnummer (Format: BW-XXXXXX)
6. Berechnet Fälligkeitsdatum (+30 Tage)
7. Berechnet Steuerbeträge (19% MwSt.)
8. Speichert Gebühr in Datenbank

**Validierungen:**
- Angebot muss existieren
- Angebot muss Status "ACCEPTED" haben
- Gebührenbetrag darf nicht negativ sein
- Keine Duplikate (pro Quote nur eine Gebühr)

#### Weitere wichtige Methoden:

**`get_fees_for_service_provider()`**
- Lädt alle Gebühren für einen bestimmten Dienstleister
- Wird für /buildwise-fees Ansicht verwendet
- Sortiert nach Fälligkeitsdatum (neueste zuerst)

**`check_overdue_fees()`**
- Prüft automatisch auf überfällige Gebühren
- Markiert Gebühren als 'overdue' wenn Fälligkeitsdatum überschritten
- Sollte als Cronjob täglich ausgeführt werden

**`mark_as_paid()`**
- Markiert eine Gebühr als bezahlt
- Setzt Zahlungsdatum und ändert Status zu 'paid'

### API-Endpoints

**Datei:** `app/api/buildwise_fees.py`

#### GET `/api/v1/buildwise-fees/`
Lädt BuildWise-Gebühren mit Filtern

**Parameter:**
- `skip` - Pagination Offset (Standard: 0)
- `limit` - Anzahl Ergebnisse (Standard: 100, Max: 1000)
- `project_id` - Filter nach Projekt
- `status` - Filter nach Status ('open', 'paid', 'overdue', 'cancelled')
- `month` - Filter nach Monat (1-12)
- `year` - Filter nach Jahr

**Berechtigungen:**
- Dienstleister: Sehen nur eigene Gebühren
- Bauträger/Admin: Sehen alle Gebühren (mit Filtern)

**Response:**
```json
[
  {
    "id": 1,
    "invoice_number": "BW-000001",
    "quote_id": 42,
    "project_id": 10,
    "service_provider_id": 5,
    "fee_amount": 470.00,
    "fee_percentage": 4.7,
    "quote_amount": 10000.00,
    "currency": "EUR",
    "invoice_date": "2025-10-01",
    "due_date": "2025-10-31",
    "status": "open",
    "tax_rate": 19.0,
    "tax_amount": 89.30,
    "net_amount": 470.00,
    "gross_amount": 559.30,
    "fee_details": "BuildWise Vermittlungsgebühr (4.7%) für akzeptiertes Angebot 'Sanitärarbeiten'",
    "notes": "Automatisch generiert bei Angebotsannahme am 01.10.2025. Fällig am 31.10.2025."
  }
]
```

#### GET `/api/v1/buildwise-fees/{fee_id}`
Lädt eine spezifische Gebühr

#### POST `/api/v1/buildwise-fees/{fee_id}/mark-as-paid`
Markiert eine Gebühr als bezahlt

**Parameter:**
- `payment_date` - Optional, Zahlungsdatum (Format: YYYY-MM-DD)

#### POST `/api/v1/buildwise-fees/{fee_id}/generate-gewerk-invoice`
Generiert eine PDF-Rechnung und speichert sie als Dokument

#### GET `/api/v1/buildwise-fees/statistics`
Lädt Statistiken über alle Gebühren

**Response:**
```json
{
  "total_fees": 50,
  "total_amount": 25000.00,
  "total_paid": 15000.00,
  "total_open": 8000.00,
  "total_overdue": 2000.00,
  "monthly_breakdown": [...],
  "status_breakdown": {...}
}
```

#### POST `/api/v1/buildwise-fees/check-overdue`
Prüft auf überfällige Gebühren und markiert sie

### Integration in Quote-Akzeptierung

**Datei:** `app/services/quote_service.py`

**Funktion:** `accept_quote()`

```python
# Nach Angebot-Akzeptierung:
# 1. Erstelle Kostenposition (für Finanzen-Übersicht)
cost_position = await create_cost_position_from_quote(db, quote)

# 2. Erstelle BuildWise-Gebühr
buildwise_fee = await BuildWiseFeeService.create_fee_from_quote(
    db=db,
    quote_id=quote.id,
    cost_position_id=cost_position_id,
    fee_percentage=None  # Verwendet automatisch 4.7% in Production
)
```

**Fehlerbehandlung:**
- Wenn Kostenposition-Erstellung fehlschlägt, wird eine Dummy-Kostenposition erstellt
- Fehler bei Gebühren-Erstellung blockieren nicht die Angebots-Akzeptierung
- Alle Fehler werden geloggt für spätere Analyse

### Konfiguration

**Datei:** `app/core/config.py`

**Umgebungsmodi:**

```python
environment_mode: Literal["beta", "production"] = "beta"
```

**Provisionssätze:**
- **Beta-Modus**: 0% (keine Gebühren)
- **Production-Modus**: 4.7%

**Funktion:** `get_fee_percentage()`

```python
def get_fee_percentage(self) -> float:
    if self.environment_mode == "beta":
        return 0.0
    elif self.environment_mode == "production":
        return 4.7
    return self.buildwise_fee_percentage
```

**Konfigurationsdatei:** `environment_config.json`

```json
{
  "environment_mode": "production",
  "buildwise_fee_percentage": 4.7,
  "buildwise_fee_enabled": true
}
```

## Best Practices

### 1. Fehlerbehandlung

✅ **DO:**
```python
try:
    buildwise_fee = await BuildWiseFeeService.create_fee_from_quote(...)
    print(f"✅ Gebühr erstellt: {buildwise_fee.invoice_number}")
except ValueError as ve:
    print(f"⚠️ Validierungsfehler: {ve}")
    # Bereits existierende Gebühr oder ungültige Daten
except Exception as e:
    print(f"❌ Unerwarteter Fehler: {e}")
    # Kritischer Fehler, evtl. Rollback
```

❌ **DON'T:**
```python
# Fehler ignorieren ohne Logging
buildwise_fee = await BuildWiseFeeService.create_fee_from_quote(...)
```

### 2. Validierung

✅ **Immer validieren:**
- Angebot existiert
- Angebot ist akzeptiert
- Keine Duplikate
- Gebührenbetrag ist positiv
- Fälligkeitsdatum liegt in der Zukunft

### 3. Logging

✅ **Strukturiertes Logging:**
```python
print(f"🔧 [BuildWiseFeeService] Erstelle Gebühr für Quote {quote_id}")
print(f"   - Quote Amount: {quote_amount} EUR")
print(f"   - Fee Percentage: {fee_percentage}%")
print(f"   - Due Date: {due_date}")
```

### 4. Transaktionen

✅ **Atomare Operationen:**
```python
try:
    db.add(fee)
    await db.commit()
    await db.refresh(fee)
except Exception as e:
    await db.rollback()
    raise
```

## Testing

### Manueller Test-Workflow

1. **Angebot erstellen:**
   ```bash
   POST /api/v1/quotes
   ```

2. **Angebot akzeptieren:**
   ```bash
   POST /api/v1/quotes/{quote_id}/accept
   ```

3. **Gebühr überprüfen:**
   ```bash
   GET /api/v1/buildwise-fees/
   ```

4. **Erwartetes Ergebnis:**
   - Status: 'open'
   - fee_percentage: 4.7% (in Production)
   - due_date: heute + 30 Tage
   - Alle Beträge korrekt berechnet

### Edge Cases

**Fall 1: Angebot wird zweimal akzeptiert**
- Erste Akzeptierung: Gebühr wird erstellt
- Zweite Akzeptierung: Existierende Gebühr wird zurückgegeben (kein Fehler)

**Fall 2: Keine Kostenposition vorhanden**
- System erstellt automatisch eine Dummy-Kostenposition
- BuildWise-Gebühr wird trotzdem erstellt

**Fall 3: Beta-Modus**
- Gebühr wird mit 0% erstellt
- Alle anderen Prozesse laufen normal

**Fall 4: Überfällige Gebühr**
- Cronjob markiert als 'overdue'
- Dienstleister sieht rote Warnung in UI

## Wartung

### Tägliche Aufgaben

**Überfällige Gebühren prüfen:**
```bash
POST /api/v1/buildwise-fees/check-overdue
```

**Empfehlung:** Als Cronjob einrichten (täglich um 00:00 Uhr)

### Monatliche Aufgaben

1. **Statistiken überprüfen:**
   ```bash
   GET /api/v1/buildwise-fees/statistics
   ```

2. **Offene Gebühren kontrollieren:**
   ```bash
   GET /api/v1/buildwise-fees/?status=open
   ```

3. **Überfällige Gebühren nachverfolgen:**
   ```bash
   GET /api/v1/buildwise-fees/?status=overdue
   ```

## Troubleshooting

### Problem: Gebühr wurde nicht erstellt

**Mögliche Ursachen:**
1. Angebot wurde nicht akzeptiert
2. Gebühr existiert bereits
3. Fehler beim Speichern (DB-Problem)

**Lösung:**
```python
# Logs überprüfen
grep "BuildWiseFeeService" logs/app.log

# Manuell erstellen
POST /api/v1/buildwise-fees/create-from-quote/{quote_id}/{cost_position_id}
```

### Problem: Falsche Berechnung

**Überprüfen:**
1. Environment-Modus (beta vs. production)
2. fee_percentage in Datenbank
3. MwSt.-Satz (sollte 19% sein)

**Korrektur:**
```bash
PUT /api/v1/buildwise-fees/{fee_id}
{
  "fee_amount": 470.00,
  "tax_amount": 89.30,
  "gross_amount": 559.30
}
```

### Problem: Gebühr nicht sichtbar für Dienstleister

**Überprüfen:**
1. service_provider_id stimmt überein
2. Benutzer ist als SERVICE_PROVIDER angemeldet
3. Gebühr existiert in Datenbank

**Query:**
```sql
SELECT * FROM buildwise_fees WHERE service_provider_id = {user_id};
```

## Erweiterungen & Roadmap

### Geplante Features

1. **Automatische Zahlungserinnerungen**
   - Email 7 Tage vor Fälligkeit
   - Email am Fälligkeitstag
   - Mahnung nach 7 Tagen Überfälligkeit

2. **Ratenplanung**
   - Große Gebühren auf mehrere Raten aufteilen
   - Individuelle Zahlungspläne

3. **Rabatte & Sonderkonditionen**
   - Treuerabatte für langjährige Dienstleister
   - Mengenrabatte bei vielen Aufträgen

4. **Automatische Zahlungsabwicklung**
   - Integration mit Stripe/PayPal
   - SEPA-Lastschrift

5. **Detaillierte Analytics**
   - Dashboard für Dienstleister
   - Vergleich mit Branchendurchschnitt
   - Trends & Prognosen

## Zusammenfassung

Die BuildWise-Gebühren-Implementierung:

✅ **Automatisch** - Wird bei Angebotsannahme erstellt
✅ **Transparent** - 4.7% Provisionssatz klar kommuniziert
✅ **Flexibel** - Konfigurierbar via Environment-Modus
✅ **Robust** - Umfassende Fehlerbehandlung und Validierung
✅ **Nachvollziehbar** - Ausführliches Logging aller Schritte
✅ **Best Practices** - Folgt Clean Code und SOLID Prinzipien

---

**Erstellt am:** 01.10.2025  
**Version:** 1.0  
**Autor:** BuildWise Development Team

