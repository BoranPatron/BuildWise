# 🔒 Account-Sperre - Quick Start Guide

## Was wurde implementiert?

✅ **Automatische Kontosperre für Dienstleister mit überfälligen Rechnungen**

Wenn ein Dienstleister eine oder mehrere überfällige BuildWise-Gebühren hat, wird sein Account **vollständig gesperrt**. Die Plattform ist nicht mehr nutzbar, bis alle Rechnungen beglichen sind.

## Funktionsweise

### 🔍 Automatische Prüfung

```
Login → Account-Check → Überfällige Rechnung? → ❌ SPERRE
                                                  ↓
                                           ✅ Kein Problem → Weiter
```

**Prüfzeitpunkte:**
- Beim Login
- Beim Seitenwechsel (über ProtectedRoute)
- Alle 5 Minuten automatisch

### 🚫 Was passiert bei Sperre?

1. **Fullscreen-Modal** erscheint (rot, große Warnung)
2. **Keine Navigation** möglich
3. **Keine Features** zugänglich
4. **Nur Zahlungsoptionen** verfügbar

### 💳 Zahlungsoptionen im Modal

Für jede überfällige Rechnung:

| Button | Aktion | Ergebnis |
|--------|--------|----------|
| 🟣 **Mit Stripe bezahlen** | Weiterleitung zu Stripe Checkout | Sofortige Entsperrung nach Zahlung |
| 🔵 **Überweisung** | Zeigt Bankdaten an | Manuelle Markierung nötig |
| 🟢 **Als bezahlt markieren** | Markiert Rechnung als bezahlt | Sofortige Entsperrung |

## Beispiel-Ansicht

```
╔════════════════════════════════════════════════════╗
║  ⚠️  ACCOUNT GESPERRT                              ║
║  Überfällige Rechnungen müssen beglichen werden    ║
╠════════════════════════════════════════════════════╣
║                                                     ║
║  📊 Übersicht                                       ║
║  • Anzahl überfälliger Rechnungen: 2               ║
║  • Gesamtbetrag: 216.20 EUR                        ║
║                                                     ║
║  ─────────────────────────────────────────────────  ║
║                                                     ║
║  📄 Rechnung #BW-000123                            ║
║  📅 Fällig: 27.09.2024 | 5 Tage überfällig        ║
║  💰 108.10 EUR (inkl. MwSt.)                       ║
║                                                     ║
║  [🟣 Mit Stripe bezahlen] [🔵 Überweisung]        ║
║  [🟢 Als bezahlt markieren]                        ║
║                                                     ║
║  ┌─────────────────────────────────────────┐      ║
║  │ Überweisungsdetails:                     │      ║
║  │ IBAN: CH93 0000 0000 0000 0001 2        │      ║
║  │ Betrag: 108.10 EUR                       │      ║
║  │ Verwendungszweck: BW-000123             │      ║
║  └─────────────────────────────────────────┘      ║
║                                                     ║
║  ─────────────────────────────────────────────────  ║
║                                                     ║
║  📄 Rechnung #BW-000124                            ║
║  ... (weitere überfällige Rechnung)                ║
║                                                     ║
╚════════════════════════════════════════════════════╝
```

## Testing

### ✅ Szenario 1: Rechnung überfällig machen

**SQL (in buildwise.db ausführen):**
```sql
UPDATE buildwise_fees 
SET 
  due_date = DATE('now', '-5 days'),
  status = 'overdue'
WHERE service_provider_id = 2;  -- Dienstleister-ID
```

**Ergebnis:**
- Als Dienstleister einloggen → Account sofort gesperrt
- Modal erscheint mit Zahlungsoptionen

### ✅ Szenario 2: Zahlung testen

**Stripe-Test:**
1. Auf "Mit Stripe bezahlen" klicken
2. Stripe-Testmodus nutzen (Testkarte: `4242 4242 4242 4242`)
3. Zahlung abschließen
4. Automatische Weiterleitung zurück zur Plattform
5. **Account ist entsperrt** ✅

**Manuelle Markierung:**
1. Auf "Als bezahlt markieren" klicken
2. **Account ist sofort entsperrt** ✅
3. Page Reload erfolgt automatisch

### ✅ Szenario 3: Entsperrung prüfen

**Nach Zahlung:**
```sql
-- Prüfe Status
SELECT id, invoice_number, status, due_date, payment_date
FROM buildwise_fees
WHERE service_provider_id = 2;
```

**Status sollte jetzt sein:** `paid`

## API-Endpunkte

### Check Account Status
```bash
GET /api/v1/buildwise-fees/check-account-status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "account_locked": true,
  "has_overdue_fees": true,
  "overdue_fees": [
    {
      "id": 123,
      "invoice_number": "BW-000123",
      "due_date": "2024-09-27",
      "gross_amount": 108.1,
      "days_overdue": 5
    }
  ],
  "total_overdue_amount": 108.1,
  "message": "Account gesperrt - Bitte bezahlen Sie Ihre überfälligen Rechnungen"
}
```

## Wichtige Dateien

### Backend
```
app/api/buildwise_fees.py
  └─ @router.get("/check-account-status")
```

### Frontend
```
Frontend/Frontend/src/
  ├─ api/buildwiseFeeService.ts
  │   └─ checkAccountStatus()
  ├─ components/AccountLockedModal.tsx
  │   └─ Vollbild-Sperre mit Zahlungsoptionen
  └─ App.tsx
      └─ ProtectedRoute mit Account-Check
```

## Häufige Fragen

### ❓ Werden auch Bauträger gesperrt?
**Nein**, nur Dienstleister. Bauträger sind nie betroffen.

### ❓ Was ist, wenn der Backend-Check fehlschlägt?
Der Account wird **nicht gesperrt**. Sicherheit geht vor, aber keine False-Positives.

### ❓ Kann ich die Sperre manuell umgehen?
**Nein**, Frontend und Backend prüfen. Nur durch Zahlung oder manuelle Markierung.

### ❓ Wie schnell erfolgt die Entsperrung?
- **Stripe**: Sofort nach erfolgreicher Zahlung (via Webhook)
- **Manuelle Markierung**: Sofort mit Page Reload

### ❓ Was passiert bei mehreren überfälligen Rechnungen?
**Alle werden angezeigt**. Account ist erst entsperrt, wenn **alle** bezahlt sind.

## Support-Aktionen

### 🔧 Emergency-Entsperrung (Admin)

Wenn ein Kunde dringend entsperrt werden muss:

```sql
-- Option 1: Alle Rechnungen als bezahlt markieren
UPDATE buildwise_fees 
SET 
  status = 'paid',
  payment_date = DATE('now')
WHERE service_provider_id = [USER_ID] AND status = 'overdue';

-- Option 2: Fälligkeitsdatum verschieben
UPDATE buildwise_fees 
SET 
  due_date = DATE('now', '+30 days'),
  status = 'open'
WHERE service_provider_id = [USER_ID] AND status = 'overdue';
```

### 📊 Account-Status prüfen

```bash
# Als Admin/Support
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/buildwise-fees/check-account-status"
```

## Logs & Debugging

### Browser Console
```javascript
// Account-Status manuell prüfen
const status = await checkAccountStatus();
console.log('Account Status:', status);
```

### Backend Logs
```bash
# Grep nach Account-Check
grep "Account-Status" app.log

# Grep nach Sperr-Events
grep "account_locked" app.log
```

---

## ✅ Status: Produktionsbereit

**Version**: 1.0  
**Getestet**: ✅ Lokal  
**Dokumentiert**: ✅ Vollständig  
**Deployment**: ✅ Ready

Bei Fragen: Siehe `ACCOUNT_SPERRE_IMPLEMENTIERUNG.md` für Details.


