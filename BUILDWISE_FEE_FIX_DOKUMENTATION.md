# BuildWise-Gebühren Fix - Dokumentation

## Problem
Wenn ein Bauträger ein Angebot akzeptiert hat, wurde das Quote zwar auf Status `ACCEPTED` gesetzt, aber **keine BuildWise-Gebühr** in der Tabelle `buildwise_fees` erstellt.

## Ursache
Der Code zur automatischen Erstellung von BuildWise-Gebühren existierte bereits im `accept_quote` Service, aber er schlug **silent** fehl aufgrund eines **Rundungsfehlers**:

1. **Berechnung**: `1234 CHF * 4.7% = 57.998 CHF`
2. **Problem**: Pydantic-Schema erwartet Decimal mit **maximal 2 Dezimalstellen**
3. **Fehler**: `Decimal('57.998')` hat 3 Dezimalstellen → Pydantic ValidationError
4. **Resultat**: Die Gebühr wurde nicht erstellt, aber das Quote wurde trotzdem akzeptiert (by design, um die Hauptfunktion nicht zu blockieren)

## Lösung

### 1. Rundungsfehler behoben
**Datei**: `app/services/buildwise_fee_service.py`

```python
# Berechne die Gebühr
quote_amount = float(quote.total_amount)
fee_amount_raw = quote_amount * (fee_percentage / 100.0)

# WICHTIG: Runde auf 2 Dezimalstellen, um Pydantic-Validierungsfehler zu vermeiden
fee_amount = round(fee_amount_raw, 2)
```

**Vorher**: `fee_amount = quote_amount * (fee_percentage / 100.0)` → Rundungsfehler möglich  
**Nachher**: Explizite Rundung auf 2 Dezimalstellen

### 2. Verbessertes Logging
**Datei**: `app/services/quote_service.py`

Detaillierte Logs wurden hinzugefügt um zukünftige Probleme schneller zu identifizieren:

```python
print(f"\n{'='*80}")
print(f"[QuoteService] ERSTELLE BUILDWISE GEBUEHR FÜR QUOTE {quote.id}")
print(f"{'='*80}")
print(f"   Quote ID: {quote.id}")
print(f"   Quote Amount: {quote.total_amount} {quote.currency}")
print(f"   Service Provider ID: {quote.service_provider_id}")
print(f"   Fee Percentage: {get_fee_percentage()}%")
# ... mehr Details
```

### 3. Retry-Logik mit besserer Fehlerbehandlung
**Datei**: `app/services/quote_service.py`

```python
# Erstelle BuildWise Gebühr mit Retry-Logik
max_retries = 3
for attempt in range(max_retries):
    try:
        # Versuche Gebühr zu erstellen
        buildwise_fee = await BuildWiseFeeService.create_fee_from_quote(...)
        buildwise_fee_created = True
        break
    except ValueError as ve:
        # Spezifische Fehlerbehandlung für Validierungsfehler
        if "Pydantic" in error_msg or "validation" in error_msg.lower():
            print(f"[QuoteService] FEHLER: Pydantic-Validierungsfehler")
            # ... detaillierte Logs
```

## Testing

### Manuelle Erstellung für existierendes Quote
Für Quote 1 (das bereits akzeptiert war, aber keine Gebühr hatte):

```bash
python create_buildwise_fee_manually.py
```

**Resultat**:
- Fee ID: 1
- Rechnungsnummer: BW-000001
- Nettobetrag: 58.00 CHF (4.7% von 1234 CHF)
- Bruttobetrag: 62.70 CHF (inkl. 8.1% MwSt)
- Status: open
- Fällig: 01.11.2025 (+30 Tage)

### Automatischer Test für neues Quote
```bash
python test_quote_accept_with_fee.py
```

**Resultat**:
- Neues Test-Quote erstellt (ID: 2, Betrag: 5000 CHF)
- Quote akzeptiert → Status: ACCEPTED
- BuildWise-Gebühr **automatisch** erstellt:
  - Fee ID: 2
  - Rechnungsnummer: BW-000002
  - Nettobetrag: 235.00 CHF (4.7% von 5000 CHF)
  - Bruttobetrag: 254.04 CHF
  - Status: open

## Datenbank-Überprüfung

```bash
python check_quote_fee.py
```

**Ausgabe**:
```
ALL BUILDWISE FEES IN DATABASE
Fee ID: 1, Quote ID: 1, Invoice: BW-000001, Amount: 58, Status: open
Fee ID: 2, Quote ID: 2, Invoice: BW-000002, Amount: 235, Status: open
```

## Verifizierung im Frontend

Nach dem Fix sollten BuildWise-Gebühren im Frontend sichtbar sein:

1. Als **Bauträger** einloggen
2. Zu `/buildwise-fees` navigieren
3. Gebühren sollten angezeigt werden mit:
   - Rechnungsnummer
   - Betrag (Netto/Brutto)
   - Status
   - Fälligkeitsdatum
   - Projekt-/Quote-Referenz

## Konfiguration

Die Gebührenhöhe wird aus der Konfiguration gelesen:

**Datei**: `app/core/config.py`

```python
def get_fee_percentage() -> float:
    """
    Gibt den aktuellen BuildWise-Gebührenprozentsatz zurück.
    
    - Production: 4.7%
    - Beta/Test: 0% (keine Gebühren)
    """
    environment_mode = getattr(settings, 'environment_mode', 'production')
    
    if environment_mode in ('beta', 'test', 'development'):
        return 0.0  # Keine Gebühren im Beta/Test-Modus
    else:
        return 4.7  # 4.7% in Production
```

## Wichtige Hinweise

1. **Non-Blocking**: Das Fehlschlagen der Gebührenerstellung blockiert **nicht** die Quote-Akzeptierung
2. **Idempotent**: Wenn eine Gebühr bereits existiert, wird keine zweite erstellt
3. **Automatisch**: Bei jedem Quote-Accept wird automatisch versucht, eine Gebühr zu erstellen
4. **Manueller Fallback**: Falls automatisch fehlgeschlagen, kann mit `create_buildwise_fee_manually.py` manuell nachgeholt werden

## Betroffene Dateien

### Geändert
- ✅ `app/services/buildwise_fee_service.py` (Rundung hinzugefügt)
- ✅ `app/services/quote_service.py` (Verbessertes Logging und Fehlerbehandlung)

### Neu erstellt (für Testing/Debugging)
- ✅ `check_quote_fee.py` (Datenbank-Überprüfung)
- ✅ `create_buildwise_fee_manually.py` (Manuelle Gebührenerstellung)
- ✅ `test_quote_accept_with_fee.py` (Automatischer Test)
- ✅ `BUILDWISE_FEE_FIX_DOKUMENTATION.md` (Diese Datei)

## Nächste Schritte

1. ✅ Problem identifiziert und behoben
2. ✅ Logging verbessert
3. ✅ Tests erstellt und erfolgreich durchgeführt
4. ⏳ Backend neu starten (falls läuft)
5. ⏳ Im Frontend testen:
   - Neues Angebot von Dienstleister erstellen
   - Als Bauträger akzeptieren
   - Prüfen ob Gebühr in `/buildwise-fees` erscheint

## Stripe-Integration (falls aktiviert)

Falls Stripe aktiviert ist, können Dienstleister ihre Gebühren direkt bezahlen:

1. BuildWise-Gebühr wird erstellt (Status: `open`)
2. Dienstleister sieht Gebühr in `/buildwise-fees`
3. "Jetzt bezahlen" Button erstellt Stripe Checkout Session
4. Nach erfolgreicher Zahlung: Status → `paid`
5. Account-Sperre wird aufgehoben (falls überfällig war)

## Gebührenberechnung

```
Nettobetrag = Quote-Betrag * 4.7%
MwSt (8.1%) = Nettobetrag * 8.1%
Bruttobetrag = Nettobetrag + MwSt

Beispiel:
Quote: 1234 CHF
→ Netto: 58.00 CHF (4.7%)
→ MwSt: 4.70 CHF (8.1%)
→ Brutto: 62.70 CHF
```

## Support

Bei Problemen:
1. Backend-Logs überprüfen (detaillierte Ausgaben bei Quote-Accept)
2. Datenbank überprüfen: `python check_quote_fee.py`
3. Manuell nachhelfen: `python create_buildwise_fee_manually.py`
4. Diese Dokumentation konsultieren

---
**Status**: ✅ Implementiert und getestet  
**Datum**: 02.10.2025  
**Version**: 1.0



