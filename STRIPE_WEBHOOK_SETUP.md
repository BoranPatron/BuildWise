# 🔗 Stripe Webhook Setup - Schritt-für-Schritt Anleitung

## 📋 Übersicht

Diese Anleitung zeigt, wie du den Stripe Webhook für automatische Zahlungsbestätigungen einrichtest.

## 🚀 Lokale Entwicklung (Sofort testbar)

### Option 1: Stripe CLI (Empfohlen für Tests)

1. **Stripe CLI installieren:**
   ```bash
   # Windows (via Chocolatey)
   choco install stripe-cli
   
   # Oder manuell von: https://github.com/stripe/stripe-cli/releases
   ```

2. **Bei Stripe anmelden:**
   ```bash
   stripe login
   ```

3. **Webhook forwarding starten:**
   ```bash
   # In neuem Terminal (parallel zum Backend)
   stripe listen --forward-to localhost:8000/api/v1/buildwise-fees/stripe-webhook
   ```

4. **Webhook Secret kopieren:**
   ```
   > Ready! Your webhook signing secret is whsec_1234567890abcdef...
   ```

5. **Secret in Config eintragen:**
   ```python
   # In app/core/config.py:
   stripe_webhook_secret: str = "whsec_1234567890abcdef..."
   ```

6. **Backend neu starten:**
   ```bash
   python .\start_backend.py
   ```

7. **Testen:**
   - Stripe-Button im Frontend klicken
   - Test-Zahlung durchführen
   - Webhook wird automatisch weitergeleitet
   - Gebühr wird als "bezahlt" markiert

### Option 2: ngrok (Alternative)

1. **ngrok installieren:** https://ngrok.com/download

2. **Backend öffentlich machen:**
   ```bash
   ngrok http 8000
   ```

3. **Öffentliche URL notieren:**
   ```
   https://abc123.ngrok.io
   ```

4. **Webhook in Stripe Dashboard erstellen** (siehe unten)

## 🌐 Production Setup

### 1. Webhook in Stripe Dashboard erstellen

1. **Gehe zu Stripe Dashboard:**
   - Test-Modus: https://dashboard.stripe.com/test/webhooks
   - Live-Modus: https://dashboard.stripe.com/webhooks

2. **"Add endpoint" klicken**

3. **Webhook konfigurieren:**
   ```
   Endpoint URL: https://your-domain.com/api/v1/buildwise-fees/stripe-webhook
   Description: BuildWise Payment Confirmations
   ```

4. **Events auswählen:**
   - ✅ `checkout.session.completed`
   - ✅ `payment_intent.succeeded` (optional)

5. **Webhook erstellen und Secret kopieren:**
   ```
   Signing secret: whsec_1234567890abcdef...
   ```

### 2. Secret in Production Config

**Option A: Environment Variable**
```bash
export STRIPE_WEBHOOK_SECRET="whsec_1234567890abcdef..."
```

**Option B: Config-Datei**
```python
# In app/core/config.py:
stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
```

**Option C: .env Datei**
```env
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef...
```

### 3. Server neu starten

```bash
# Production
systemctl restart buildwise-backend

# Oder Docker
docker-compose restart backend
```

## 🧪 Webhook testen

### 1. Test-Zahlung durchführen

1. **Frontend öffnen:** http://localhost:5173/buildwise-fees
2. **"Bezahlen"-Button klicken**
3. **Test-Kreditkarte verwenden:**
   ```
   Nummer: 4242 4242 4242 4242
   CVV: 123
   Datum: 12/34
   PLZ: 12345
   ```
4. **Zahlung bestätigen**

### 2. Logs prüfen

**Backend-Terminal:**
```
[Webhook] Stripe Webhook erhalten
[StripeService] Webhook-Signatur erfolgreich verifiziert
   - Event ID: evt_1234567890
   - Event Type: checkout.session.completed
[StripeService] Verarbeite Event: checkout.session.completed
[Webhook] ✅ Gebühr 1 erfolgreich als bezahlt markiert
   - Betrag: 559.30 CHF
   - Zahlungsmethode: card
```

**Stripe CLI (falls verwendet):**
```
2024-10-02 10:30:15   --> checkout.session.completed [evt_1234567890]
2024-10-02 10:30:15  <--  [200] POST http://localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

### 3. Frontend prüfen

- Seite automatisch aktualisieren
- Gebühr sollte als "Bezahlt" (grün) markiert sein
- Success-Message sollte erscheinen

## 🔧 Troubleshooting

### Problem: "Ungültige Webhook Signatur"

**Lösung:**
1. Prüfe Webhook Secret in Config
2. Stelle sicher, dass Secret mit `whsec_` beginnt
3. Backend neu starten nach Änderung

### Problem: "Keine fee_id in Metadaten"

**Lösung:**
1. Prüfe Payment Link Erstellung
2. Metadaten werden automatisch hinzugefügt
3. Event-Logs im Backend prüfen

### Problem: Webhook wird nicht empfangen

**Lösung:**
1. **Lokale Entwicklung:** Stripe CLI verwenden
2. **Production:** Firewall/Load Balancer prüfen
3. **URL prüfen:** Muss öffentlich erreichbar sein
4. **HTTPS:** Production benötigt SSL

### Problem: Gebühr wird nicht als bezahlt markiert

**Lösung:**
1. Backend-Logs prüfen
2. Datenbank-Verbindung prüfen
3. Manuell über Button markieren

## 📊 Webhook-Events Übersicht

### Unterstützte Events

| Event | Beschreibung | Status |
|-------|--------------|--------|
| `checkout.session.completed` | Zahlung abgeschlossen | ✅ Implementiert |
| `payment_intent.succeeded` | Payment Intent erfolgreich | ✅ Implementiert |
| `payment_intent.payment_failed` | Zahlung fehlgeschlagen | ⚠️ Geplant |

### Event-Datenstruktur

```json
{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_1234567890",
      "amount_total": 55930,
      "currency": "chf",
      "payment_intent": "pi_1234567890",
      "metadata": {
        "fee_id": "1",
        "invoice_number": "BW-000001",
        "type": "buildwise_fee"
      },
      "customer_details": {
        "email": "kunde@example.com"
      }
    }
  }
}
```

## 🔐 Sicherheit

### Best Practices

1. **Signatur-Verifizierung:** ✅ Implementiert
2. **HTTPS verwenden:** Für Production erforderlich
3. **Secret sicher speichern:** Environment Variables
4. **Idempotenz:** ✅ Doppelte Events werden ignoriert
5. **Logging:** ✅ Alle Events werden geloggt

### Webhook-Sicherheit

- ✅ Signatur-Verifizierung mit Stripe Secret
- ✅ Zeitstempel-Toleranz (5 Minuten)
- ✅ Robuste Fehlerbehandlung
- ✅ Immer HTTP 200 zurückgeben (verhindert Retry-Loops)

## 📈 Monitoring

### Stripe Dashboard

- **Webhook-Logs:** https://dashboard.stripe.com/test/webhooks
- **Event-History:** Alle Events mit Status
- **Retry-Attempts:** Automatische Wiederholungen bei Fehlern

### Backend-Logs

```bash
# Webhook-Events filtern
tail -f backend.log | grep "\[Webhook\]"

# Stripe-Service Events
tail -f backend.log | grep "\[StripeService\]"
```

## ✅ Checkliste

### Lokale Entwicklung
- [ ] Stripe CLI installiert
- [ ] `stripe listen` läuft
- [ ] Webhook Secret in Config
- [ ] Backend neu gestartet
- [ ] Test-Zahlung erfolgreich

### Production
- [ ] Webhook in Stripe Dashboard erstellt
- [ ] Events `checkout.session.completed` ausgewählt
- [ ] Webhook Secret in Environment Variables
- [ ] HTTPS aktiviert
- [ ] Firewall konfiguriert
- [ ] Monitoring eingerichtet

---

**🎉 Webhook ist jetzt vollständig eingerichtet!**

Zahlungen werden automatisch als "bezahlt" markiert und Dienstleister erhalten sofortiges Feedback.
