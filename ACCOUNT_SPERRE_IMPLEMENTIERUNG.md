# 🔒 Account-Sperre bei überfälligen Rechnungen - Implementierung

## Übersicht

Das System sperrt automatisch Dienstleister-Accounts, wenn überfällige BuildWise-Gebühren vorhanden sind. Die Plattform wird für den betroffenen Benutzer komplett blockiert, bis alle überfälligen Rechnungen beglichen sind.

## Features

### ✅ Automatische Account-Sperre
- **Trigger**: Rechnung ist überfällig (Status `overdue` oder `open` mit überschrittenem Fälligkeitsdatum)
- **Betroffene**: Nur Dienstleister (DIENSTLEISTER-Rolle)
- **Scope**: Gesamte Plattform - keine Navigation möglich

### 🔄 Kontinuierliche Prüfung
- **Initial**: Beim Login / Seitenladen
- **Periodisch**: Alle 5 Minuten automatische Überprüfung
- **Nach Zahlung**: Sofortige Entsperrung nach erfolgreicher Zahlung

### 💳 Zahlungsoptionen im Sperr-Modal
1. **Stripe Payment** - Sofortige Kartenzahlung
2. **Überweisung** - Banküberweisung mit Anzeige der Kontodetails
3. **Als bezahlt markieren** - Manuelle Bestätigung nach Überweisung

## Backend-Implementierung

### Neuer Endpunkt: `/api/v1/buildwise-fees/check-account-status`

**Datei**: `app/api/buildwise_fees.py`

```python
@router.get("/check-account-status")
async def check_account_status(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Prüft ob der aktuelle Benutzer (Dienstleister) überfällige Rechnungen hat.
    """
```

**Response-Format**:
```json
{
  "account_locked": true,
  "has_overdue_fees": true,
  "overdue_fees": [
    {
      "id": 123,
      "invoice_number": "BW-000123",
      "due_date": "2024-10-01",
      "fee_amount": 100.0,
      "gross_amount": 108.1,
      "currency": "EUR",
      "days_overdue": 5,
      "stripe_payment_link_url": "https://checkout.stripe.com/..."
    }
  ],
  "total_overdue_amount": 108.1,
  "message": "Account gesperrt - Bitte bezahlen Sie Ihre überfälligen Rechnungen"
}
```

**Logik**:
- Nur für Dienstleister (UserRole.DIENSTLEISTER)
- Lädt alle Gebühren des Dienstleisters
- Filtert nach Status `overdue` ODER Status `open` mit `due_date < heute`
- Account ist gesperrt wenn mindestens eine überfällige Gebühr existiert

## Frontend-Implementierung

### 1. Service-Funktion

**Datei**: `Frontend/Frontend/src/api/buildwiseFeeService.ts`

```typescript
export interface AccountStatus {
  account_locked: boolean;
  has_overdue_fees: boolean;
  overdue_fees: Array<{...}>;
  total_overdue_amount: number;
  message: string;
}

export async function checkAccountStatus(): Promise<AccountStatus>
```

### 2. Sperre-Modal Komponente

**Datei**: `Frontend/Frontend/src/components/AccountLockedModal.tsx`

**Features**:
- ⚠️ Große Warnung mit rotem Design
- 📊 Übersicht über alle überfälligen Rechnungen
- 💰 Gesamtbetrag-Anzeige
- 🗓️ Tage überfällig pro Rechnung
- 💳 Drei Zahlungsbuttons pro Rechnung:
  - Stripe Payment (lila Button)
  - Überweisung (blauer Button)
  - Als bezahlt markieren (grüner Button)

**UI/UX**:
- Fullscreen-Overlay (z-index: 9999)
- Backdrop-Blur für Fokus
- Responsive Design (mobile-first)
- Loading-States für alle Aktionen
- Success/Error-Messages

### 3. Global Guard in App.tsx

**Datei**: `Frontend/Frontend/src/App.tsx`

**Integration in `ProtectedRoute`**:

```typescript
// Account-Status-Check für Dienstleister
useEffect(() => {
  const checkAccount = async () => {
    if (user?.user_role === 'DIENSTLEISTER') {
      const status = await checkAccountStatus();
      if (status.account_locked) {
        setAccountStatus(status);
      }
    }
  };
  
  checkAccount();
  const interval = setInterval(checkAccount, 5 * 60 * 1000); // Alle 5 Min
  return () => clearInterval(interval);
}, [user, isInitialized]);

// Vor children-Rendering
if (accountStatus?.account_locked) {
  return <AccountLockedModal ... />;
}
```

## User-Flow

### Szenario 1: Dienstleister mit überfälliger Rechnung

1. **Login**: Dienstleister meldet sich an
2. **Check**: System prüft automatisch Account-Status
3. **Sperre**: Wenn überfällige Rechnung → Fullscreen-Modal wird angezeigt
4. **Blockierung**: Keine Navigation möglich, nur Modal sichtbar
5. **Zahlung**: Dienstleister wählt Zahlungsmethode:
   - **Stripe**: Weiterleitung zu Stripe Checkout → automatische Entsperrung nach erfolgreicher Zahlung
   - **Überweisung**: Bankdaten werden angezeigt → manuell "Als bezahlt markieren"
   - **Als bezahlt markieren**: Sofortige Entsperrung (für Admin/Support)
6. **Entsperrung**: Nach erfolgreicher Zahlung → Page Reload → Account entsperrt

### Szenario 2: Rechnung wird während Session überfällig

1. **Aktive Session**: Dienstleister arbeitet normal
2. **Hintergrund-Check**: Alle 5 Minuten wird Account-Status geprüft
3. **Rechnung wird fällig**: System erkennt überfällige Rechnung beim nächsten Check
4. **Sofortige Sperre**: Modal erscheint → Weiterarbeit nicht möglich

## Wichtige Hinweise

### 🔐 Sicherheit
- Nur Dienstleister betroffen (Bauträger werden NICHT gesperrt)
- Backend-validierung auf jeder API-Anfrage möglich (optional)
- Token-basierte Authentifizierung bleibt aktiv

### ⚡ Performance
- Check nur bei Dienstleitern (keine unnötigen API-Calls für Bauträger)
- Caching möglich (5 Minuten Intervall)
- Keine Blockierung der UI während des Checks

### 🎨 Design
- Konsistent mit BuildWise-Design-System
- Gradient-Backgrounds: `from-[#1a1a2e]` to `from-red-600`
- Icons: Lucide React
- Responsive: Mobile & Desktop optimiert

### 🔄 Stripe-Integration
- Verwendet existierende `startPaymentProcess()` Funktion
- Success-Redirect bringt zurück zur Plattform
- Webhook aktualisiert Rechnungsstatus automatisch

## Testing

### Manueller Test

1. **Rechnung überfällig machen**:
   ```sql
   UPDATE buildwise_fees 
   SET due_date = DATE('now', '-5 days'), status = 'overdue'
   WHERE service_provider_id = [DIENSTLEISTER_ID];
   ```

2. **Als Dienstleister einloggen**:
   - Account sollte sofort gesperrt sein
   - Modal erscheint

3. **Zahlung testen**:
   - Stripe: Test-Kartennummer verwenden
   - Als bezahlt markieren: Sollte sofort entsperren

4. **Entsperrung prüfen**:
   - Nach Zahlung sollte Reload erfolgen
   - Normale Navigation wieder möglich

### API-Test

```bash
# Check Account Status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/buildwise-fees/check-account-status
```

## Zukünftige Erweiterungen

### 🎯 Optional
- [ ] Grace Period (z.B. 3 Tage nach Fälligkeit)
- [ ] E-Mail-Benachrichtigung vor Sperre
- [ ] Teilweise Sperre (nur bestimmte Features)
- [ ] Admin-Override (Account entsperren trotz offener Rechnung)
- [ ] Payment-Plan / Ratenzahlung
- [ ] Automatische Mahnungen

### 🔧 Technische Verbesserungen
- [ ] Backend-Middleware für API-Sperre (nicht nur Frontend)
- [ ] Redis-Cache für Account-Status
- [ ] WebSocket für Echtzeit-Entsperrung
- [ ] Audit-Log für Sperr-/Entsperr-Aktionen

## Dateiübersicht

### Backend
- ✅ `app/api/buildwise_fees.py` - Neuer Endpunkt `/check-account-status`

### Frontend
- ✅ `Frontend/Frontend/src/api/buildwiseFeeService.ts` - Service-Funktion
- ✅ `Frontend/Frontend/src/components/AccountLockedModal.tsx` - Sperre-Modal
- ✅ `Frontend/Frontend/src/App.tsx` - Global Guard in ProtectedRoute

## Support

Bei Fragen oder Problemen:
1. Logs prüfen: Browser Console & Backend Terminal
2. Account-Status manuell prüfen: `/api/v1/buildwise-fees/check-account-status`
3. Rechnung manuell auf `paid` setzen für Emergency-Entsperrung

---

**Status**: ✅ Vollständig implementiert und getestet
**Version**: 1.0
**Datum**: 2025-10-02


