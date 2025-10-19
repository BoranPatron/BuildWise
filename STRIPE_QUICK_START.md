# 🚀 Stripe Payment Integration - Quick Start Guide

## ⚡ Schnellstart (5 Minuten)

### 1. Datenbank-Migration ausführen

```bash
cd C:\Users\user\Documents\04_Repo\BuildWise
python add_stripe_payment_columns.py
```

**Erwartete Ausgabe:**
```
[SUCCESS] Migration erfolgreich abgeschlossen!
   - 5 neue Spalten hinzugefuegt
   - 3 Indizes erstellt
```

### 2. Backend starten

```bash
# Backend starten
cd C:\Users\user\Documents\04_Repo\BuildWise
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend starten

```bash
# Frontend starten (in neuem Terminal)
cd C:\Users\user\Documents\04_Repo\Frontend\Frontend
npm run dev
```

### 4. Testen

1. **Öffne die BuildWise Fees Seite:**
   ```
   http://localhost:5173/buildwise-fees
   ```

2. **Klicke auf den "Bezahlen"-Button** bei einer offenen Gebühr

3. **Wirst zu Stripe weitergeleitet** (Checkout-Seite)

4. **Verwende Test-Kreditkarte:**
   - Nummer: `4242 4242 4242 4242`
   - CVV: `123`
   - Ablaufdatum: `12/34`
   - PLZ: `12345`

5. **Zahlung bestätigen**

6. **Zurück zu BuildWise** - Gebühr wird als "bezahlt" markiert

## 🎯 Wichtige Endpunkte

### Backend-API:
- `POST /api/v1/buildwise-fees/{fee_id}/create-payment-link` - Erstellt Payment Link
- `GET /api/v1/buildwise-fees/{fee_id}/payment-status` - Holt Zahlungsstatus
- `POST /api/v1/buildwise-fees/stripe-webhook` - Webhook für Stripe

### Frontend:
- `/buildwise-fees` - Gebührenübersicht mit Zahlungs-Button

## 🔑 API-Schlüssel (Test-Modus)

Die Test-Schlüssel sind bereits in `app/core/config.py` konfiguriert:

- **Public Key** (Frontend): `pk_test_51RmqhBD1cfnpqPDcd...`
- **Secret Key** (Backend): `sk_test_51RmqhBD1cfnpqPDcN...`

## 🧪 Test-Szenarien

### Erfolgreiche Zahlung
```
Kreditkarte: 4242 4242 4242 4242
Ergebnis: Zahlung erfolgreich
```

### Abgelehnte Zahlung
```
Kreditkarte: 4000 0000 0000 0002
Ergebnis: Karte wird abgelehnt
```

### 3D Secure
```
Kreditkarte: 4000 0027 6000 3184
Ergebnis: Zusätzliche Authentifizierung erforderlich
```

## 🎨 UI-Features

### Zahlungs-Button
- **Farbe:** Lila-Gradient (Stripe-Branding)
- **Icon:** Kreditkarte + ExternalLink
- **States:**
  - Normal: "Bezahlen"
  - Loading: Spinner + "Lädt..."
  - Disabled: Bei bezahlten Gebühren

### Status-Updates
- **Erfolg:** Grüne Success-Message nach Zahlung
- **Fehler:** Rote Error-Message bei Problemen
- **Loading:** Automatische Datenaktualisierung

## 📊 Monitoring

### Backend-Logs prüfen:
```bash
# Im Backend-Terminal sehen Sie:
[StripeService] Erstelle Payment Link für Gebühr 123
[API] Payment Link erfolgreich erstellt
[Webhook] Stripe Webhook erhalten
[Webhook] Gebühr 123 als bezahlt markiert
```

### Frontend-Logs prüfen:
```bash
# Im Browser-Console (F12):
[StripeService] Starte Zahlungsprozess für Gebühr 123
[StripeService] Payment Link erfolgreich erstellt
```

## 🐛 Troubleshooting

### Problem: "Payment Link konnte nicht erstellt werden"
**Lösung:** Prüfe ob Stripe installiert ist:
```bash
pip list | grep stripe
# Sollte zeigen: stripe 7.4.0
```

### Problem: "Nicht authentifiziert"
**Lösung:** Neu einloggen im Frontend

### Problem: Zahlung wird nicht als "bezahlt" markiert
**Lösung:** 
1. Warte 5-10 Sekunden (Webhook-Verarbeitung)
2. Seite manuell aktualisieren
3. Manuell über Button "Als bezahlt markieren"

## 🔗 Nützliche Links

- [Vollständige Dokumentation](STRIPE_INTEGRATION_DOKUMENTATION.md)
- [Stripe Dashboard (Test)](https://dashboard.stripe.com/test)
- [Stripe API Docs](https://docs.stripe.com/)
- [Payment Links Guide](https://stripe.com/docs/payment-links)

## ✅ Checkliste

- [x] Datenbank-Migration ausgeführt
- [x] Stripe-Library installiert (`stripe==7.4.0`)
- [x] Backend läuft auf Port 8000
- [x] Frontend läuft auf Port 5173
- [x] Test-Zahlung erfolgreich durchgeführt

## 🎉 Fertig!

Die Stripe-Integration ist jetzt vollständig eingerichtet und einsatzbereit!

**Nächste Schritte:**
1. Teste verschiedene Zahlungsszenarien
2. Prüfe Webhook-Logs
3. Für Production: Webhook-Endpunkt öffentlich machen
4. Für Production: Echte Stripe-Keys verwenden

---

**Fragen?** Siehe [STRIPE_INTEGRATION_DOKUMENTATION.md](STRIPE_INTEGRATION_DOKUMENTATION.md)

