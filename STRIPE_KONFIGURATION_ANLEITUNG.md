# 💳 Stripe-Konfiguration für BuildWise - Schritt-für-Schritt Anleitung

## 📋 Übersicht

Diese Anleitung führt Sie durch die komplette Einrichtung von Stripe für BuildWise Pro-Abonnements mit CHF als Währung.

## 🚀 Schritt 1: Stripe-Account erstellen

### **1.1 Registrierung**
1. Gehen Sie zu [stripe.com](https://stripe.com)
2. Klicken Sie auf "Jetzt starten"
3. Erstellen Sie ein Konto mit Ihrer E-Mail-Adresse
4. Bestätigen Sie Ihre E-Mail-Adresse

### **1.2 Schweizer Unternehmen verifizieren**
1. Gehen Sie zu **Einstellungen** → **Geschäftsinformationen**
2. Wählen Sie **Land: Schweiz**
3. Geben Sie Ihre Unternehmensdaten ein:
   - Firmenname
   - Adresse
   - UID-Nummer (falls vorhanden)
   - Bankverbindung (Schweizer Bank)

### **1.3 CHF als Haupt-Währung einstellen**
1. Gehen Sie zu **Einstellungen** → **Kontoeinstellungen**
2. Unter **Standard-Währung** wählen Sie **CHF (Schweizer Franken)**
3. Speichern Sie die Einstellungen

## 🏗️ Schritt 2: Produkte und Preise erstellen

### **2.1 Über das Dashboard**

#### **Produkt 1: BuildWise Pro Monthly**
1. Gehen Sie zu **Produkte** → **Neues Produkt hinzufügen**
2. **Name:** `BuildWise Pro Monthly`
3. **Beschreibung:** `Monatliches Pro-Abonnement für BuildWise`
4. **Preis:** `12.99 CHF`
5. **Abrechnungsmodell:** `Wiederkehrend`
6. **Intervall:** `Monatlich`
7. Klicken Sie auf **Produkt erstellen**
8. **Notieren Sie die Price ID** (z.B. `price_1234567890abcdef`)

#### **Produkt 2: BuildWise Pro Yearly**
1. Gehen Sie zu **Produkte** → **Neues Produkt hinzufügen**
2. **Name:** `BuildWise Pro Yearly`
3. **Beschreibung:** `Jährliches Pro-Abonnement für BuildWise (16% Ersparnis)`
4. **Preis:** `130.00 CHF`
5. **Abrechnungsmodell:** `Wiederkehrend`
6. **Intervall:** `Jährlich`
7. Klicken Sie auf **Produkt erstellen**
8. **Notieren Sie die Price ID** (z.B. `price_0987654321fedcba`)

### **2.2 Über die Stripe CLI (Alternative)**

```bash
# Stripe CLI installieren (falls noch nicht vorhanden)
# https://stripe.com/docs/stripe-cli

# Anmelden
stripe login

# Produkt 1: Monatlich
stripe products create \
  --name "BuildWise Pro Monthly" \
  --description "Monatliches Pro-Abonnement für BuildWise"

# Preis für monatliches Produkt (Produkt-ID aus vorherigem Befehl verwenden)
stripe prices create \
  --product prod_XXXXXXXXXX \
  --unit-amount 1299 \
  --currency chf \
  --recurring interval=month

# Produkt 2: Jährlich
stripe products create \
  --name "BuildWise Pro Yearly" \
  --description "Jährliches Pro-Abonnement für BuildWise"

# Preis für jährliches Produkt
stripe prices create \
  --product prod_YYYYYYYYYY \
  --unit-amount 13000 \
  --currency chf \
  --recurring interval=year
```

## 🔗 Schritt 3: Webhook-Endpoints konfigurieren

### **3.1 Webhook-Endpoint erstellen**
1. Gehen Sie zu **Entwickler** → **Webhooks**
2. Klicken Sie auf **Endpoint hinzufügen**
3. **Endpoint-URL:** `https://yourdomain.com/api/v1/webhooks/stripe`
   - Für lokale Entwicklung: `https://your-ngrok-url.ngrok.io/api/v1/webhooks/stripe`
4. **Events auswählen:**
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.created`
   - `customer.updated`

### **3.2 Webhook-Secret notieren**
1. Nach dem Erstellen des Webhooks klicken Sie darauf
2. Im **Signing secret** Bereich klicken Sie auf **Reveal**
3. **Notieren Sie das Webhook-Secret** (beginnt mit `whsec_`)

## 🔑 Schritt 4: API-Schlüssel abrufen

### **4.1 Test-Modus (Development)**
1. Gehen Sie zu **Entwickler** → **API-Schlüssel**
2. Stellen Sie sicher, dass **Test-Daten anzeigen** aktiviert ist
3. **Notieren Sie:**
   - **Publishable Key:** `pk_test_...`
   - **Secret Key:** `sk_test_...`

### **4.2 Live-Modus (Production)**
1. Deaktivieren Sie **Test-Daten anzeigen**
2. **Notieren Sie:**
   - **Publishable Key:** `pk_live_...`
   - **Secret Key:** `sk_live_...`

## ⚙️ Schritt 5: Environment Variables konfigurieren

### **5.1 .env Datei erweitern**

Fügen Sie folgende Zeilen zu Ihrer `.env` Datei hinzu:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_51XXXXXXXXXX  # Ihr Publishable Key
STRIPE_SECRET_KEY=sk_test_51XXXXXXXXXX       # Ihr Secret Key
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXX       # Ihr Webhook Secret

# Stripe Price IDs
STRIPE_PRO_MONTHLY_PRICE_ID=price_XXXXXXXXXX  # Monthly Price ID
STRIPE_PRO_YEARLY_PRICE_ID=price_YYYYYYYYYY   # Yearly Price ID

# URLs für Checkout Success/Cancel
FRONTEND_URL=http://localhost:5173
```

### **5.2 Beispiel mit echten Werten**

```env
# Stripe Configuration (Test-Modus)
STRIPE_PUBLISHABLE_KEY=pk_test_51MoMhKJKjHgLkJhGfDsAqWxVzCvBnMpLkJhGfDsAqWxVzCvBn
STRIPE_SECRET_KEY=sk_test_51MoMhKJKjHgLkJhGfDsAqWxVzCvBnMpLkJhGfDsAqWxVzCvBn
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdefghijklmnopqrstuvwxyz1234567890

# Stripe Price IDs
STRIPE_PRO_MONTHLY_PRICE_ID=price_1MoMhKJKjHgLkJhGfDsAqWx
STRIPE_PRO_YEARLY_PRICE_ID=price_1MoMhLLLjHgLkJhGfDsAqWy

# URLs
FRONTEND_URL=http://localhost:5173
```

## 🧪 Schritt 6: Test-Setup (Entwicklung)

### **6.1 Stripe CLI für lokale Webhooks**

```bash
# Stripe CLI Webhook-Forwarding für lokale Entwicklung
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# Das generiert ein temporäres Webhook-Secret für lokale Tests
# Verwenden Sie dieses Secret in Ihrer lokalen .env Datei
```

### **6.2 Test-Kreditkarten**

Für Tests verwenden Sie diese Kreditkarten-Nummern:

```
Erfolgreiche Zahlung:
- 4242 4242 4242 4242 (Visa)
- 5555 5555 5555 4444 (Mastercard)

Fehlgeschlagene Zahlung:
- 4000 0000 0000 0002 (Card declined)

3D Secure Test:
- 4000 0000 0000 3220 (3D Secure required)

Beliebiges zukünftiges Datum als Ablaufdatum
Beliebige 3-stellige CVC
```

## 🌐 Schritt 7: Ngrok für lokale Entwicklung (Optional)

### **7.1 Ngrok installieren**
1. Gehen Sie zu [ngrok.com](https://ngrok.com)
2. Erstellen Sie ein kostenloses Konto
3. Laden Sie ngrok herunter
4. Authentifizieren Sie sich: `ngrok authtoken YOUR_TOKEN`

### **7.2 Tunnel für Backend erstellen**
```bash
# Terminal 1: Backend starten
cd BuildWise
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Ngrok-Tunnel erstellen
ngrok http 8000

# Notieren Sie die HTTPS-URL (z.B. https://abc123.ngrok.io)
```

### **7.3 Webhook-URL aktualisieren**
1. Gehen Sie zu Stripe Dashboard → Webhooks
2. Bearbeiten Sie Ihren Webhook
3. Ändern Sie die URL zu: `https://abc123.ngrok.io/api/v1/webhooks/stripe`

## 🔒 Schritt 8: Sicherheits-Einstellungen

### **8.1 Webhook-Signatur-Verifizierung**
- Unser Code verifiziert automatisch Webhook-Signaturen
- Niemals das Webhook-Secret in den Code committen
- Verwenden Sie Environment Variables

### **8.2 HTTPS in Production**
- Stripe erfordert HTTPS für Webhooks in Production
- Stellen Sie sicher, dass Ihre Domain ein gültiges SSL-Zertifikat hat

### **8.3 Fehlerbehandlung**
- Implementieren Sie Retry-Logik für fehlgeschlagene Webhook-Calls
- Loggen Sie alle Stripe-Ereignisse für Debugging

## 🚦 Schritt 9: Testing-Checkliste

### **9.1 Basis-Tests**
- [ ] Stripe Dashboard zeigt Produkte korrekt an
- [ ] Price IDs sind in .env konfiguriert
- [ ] Webhook-Endpoint antwortet (200 OK)
- [ ] Test-Zahlung funktioniert
- [ ] Webhook-Events werden empfangen

### **9.2 Integration-Tests**
- [ ] Checkout-Session wird erstellt
- [ ] Erfolgreiche Zahlung aktiviert Subscription
- [ ] Fehlgeschlagene Zahlung wird korrekt behandelt
- [ ] Subscription-Kündigung funktioniert
- [ ] User wird von Basis zu Pro upgegradet

### **9.3 UI-Tests**
- [ ] Pro-Button erscheint für Bauträger
- [ ] UpgradeModal öffnet sich
- [ ] Stripe Checkout öffnet sich
- [ ] Success/Cancel-Redirects funktionieren
- [ ] Dashboard zeigt Pro-Features

## 🎯 Schritt 10: Production-Deployment

### **10.1 Live-Modus aktivieren**
1. Stripe Dashboard → **Live-Modus aktivieren**
2. Aktualisieren Sie .env mit Live-Keys:
   ```env
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   STRIPE_SECRET_KEY=sk_live_...
   ```

### **10.2 Webhook-URL für Production**
1. Aktualisieren Sie Webhook-URL zu Ihrer Production-Domain
2. Testen Sie Webhook-Delivery im Stripe Dashboard

### **10.3 Monitoring**
- Überwachen Sie Stripe Dashboard für Zahlungen
- Implementieren Sie Alerting für fehlgeschlagene Webhooks
- Loggen Sie alle Subscription-Änderungen

## 🆘 Troubleshooting

### **Häufige Probleme:**

**1. Webhook wird nicht empfangen**
- Prüfen Sie die URL im Stripe Dashboard
- Stellen Sie sicher, dass der Endpoint erreichbar ist
- Überprüfen Sie Firewall-Einstellungen

**2. Signature-Verifizierung fehlgeschlagen**
- Webhook-Secret korrekt in .env?
- Raw Request Body verwenden (nicht JSON-parsed)

**3. Checkout-Session kann nicht erstellt werden**
- Price IDs korrekt?
- Customer existiert in Stripe?
- Währung stimmt überein (CHF)?

**4. Subscription wird nicht aktiviert**
- Webhook-Events konfiguriert?
- User-ID in Metadata korrekt?
- Datenbank-Update fehlgeschlagen?

### **Debug-Commands:**

```bash
# Stripe CLI Events anzeigen
stripe events list

# Webhook-Delivery testen
stripe webhooks test

# Subscription-Status prüfen
stripe subscriptions retrieve sub_XXXXXXXXXX

# Customer-Details anzeigen
stripe customers retrieve cus_XXXXXXXXXX
```

## 📞 Support

### **Stripe-Support:**
- [Stripe-Dokumentation](https://stripe.com/docs)
- [Stripe-Support-Chat](https://dashboard.stripe.com)
- [Stripe-Community](https://github.com/stripe/stripe-node/discussions)

### **BuildWise-spezifisch:**
- Überprüfen Sie Console-Logs im Browser
- Schauen Sie sich Backend-Logs an
- Testen Sie API-Endpoints mit Postman/Insomnia

---

**✅ Nach Abschluss dieser Anleitung haben Sie:**
- Vollständig konfiguriertes Stripe-Konto
- Funktionierende CHF-Produkte
- Webhook-Integration
- Test- und Production-Setup
- Monitoring und Debugging-Tools

**🎉 Ihr BuildWise Pro-Abonnement ist bereit für den Einsatz!** 