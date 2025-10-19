# 🚀 BuildWise Deployment Konfiguration

## Umgebungsvariablen für render.com

### Wichtige Variablen für Stripe-Integration

```bash
# Frontend URL (Deine offizielle Domain)
FRONTEND_URL=https://buildwise.yourdomain.com

# Stripe Keys (Production)
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Environment Mode
ENVIRONMENT_MODE=production
BUILDWISE_FEE_PERCENTAGE=4.7
```

---

## 📋 Vollständige Umgebungsvariablen-Liste

### 1. Frontend URL
```bash
FRONTEND_URL=https://buildwise.yourdomain.com
```
**Wichtig:** Diese Variable steuert automatisch die Stripe Success/Cancel URLs:
- Success: `{FRONTEND_URL}/service-provider/buildwise-fees?payment=success`
- Cancel: `{FRONTEND_URL}/service-provider/buildwise-fees?payment=cancelled`

### 2. Database
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

### 3. Security
```bash
SECRET_KEY=ein-super-sicherer-random-string
JWT_SECRET_KEY=ein-anderer-super-sicherer-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. CORS
```bash
CORS_ORIGINS=["https://buildwise.yourdomain.com"]
```

### 5. Stripe Configuration
```bash
# Production Keys
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx

# Webhook Secret (aus Stripe Dashboard)
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_WEBHOOK_TOLERANCE=300
```

### 6. BuildWise Gebühren
```bash
ENVIRONMENT_MODE=production
BUILDWISE_FEE_PERCENTAGE=4.7
BUILDWISE_FEE_ENABLED=true
```

### 7. OAuth (Optional)
```bash
# Google OAuth
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=https://buildwise.yourdomain.com/auth/google/callback

# Microsoft OAuth
MICROSOFT_CLIENT_ID=xxx
MICROSOFT_CLIENT_SECRET=xxx
MICROSOFT_REDIRECT_URI=https://buildwise.yourdomain.com/auth/microsoft/callback
```

---

## 🔧 Stripe Webhook Setup für Production

### Schritt 1: Webhook in Stripe Dashboard erstellen

1. Gehe zu: https://dashboard.stripe.com/webhooks
2. Klicke: "Add endpoint"
3. **Endpoint URL:** `https://your-backend-url.onrender.com/api/v1/buildwise-fees/stripe-webhook`
4. **Events to send:** Wähle:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Klicke: "Add endpoint"

### Schritt 2: Webhook Secret kopieren

1. Nach dem Erstellen zeigt Stripe das **Signing Secret**
2. Es beginnt mit `whsec_xxx`
3. Kopiere es und setze es in render.com als `STRIPE_WEBHOOK_SECRET`

---

## 📝 render.com Setup Schritt-für-Schritt

### 1. Backend Deployment

1. Erstelle neuen Web Service in render.com
2. Verbinde dein GitHub Repository
3. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start Command:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. **Environment Variables:** Füge alle oben genannten Variablen hinzu

### 2. Frontend Deployment

1. Erstelle neuen Static Site in render.com
2. Verbinde dein GitHub Repository (Frontend-Ordner)
3. **Build Command:**
   ```bash
   npm install && npm run build
   ```
4. **Publish Directory:** `dist`

### 3. Domain Setup

1. Füge Custom Domain hinzu (z.B. `buildwise.yourdomain.com`)
2. Aktualisiere `FRONTEND_URL` in Backend Environment Variables
3. Aktualisiere `CORS_ORIGINS` in Backend Environment Variables

---

## ✅ Checkliste vor Deployment

- [ ] Alle Umgebungsvariablen in render.com gesetzt
- [ ] `FRONTEND_URL` zeigt auf die richtige Production-Domain
- [ ] Stripe Webhook in Stripe Dashboard erstellt
- [ ] `STRIPE_WEBHOOK_SECRET` von Stripe Dashboard kopiert
- [ ] Production Stripe Keys (`sk_live_xxx`, `pk_live_xxx`) verwenden
- [ ] Database URL auf PostgreSQL umgestellt (nicht SQLite)
- [ ] `ENVIRONMENT_MODE=production` gesetzt
- [ ] `BUILDWISE_FEE_PERCENTAGE=4.7` gesetzt
- [ ] CORS Origins auf Production-Domain aktualisiert
- [ ] OAuth Redirect URIs auf Production-Domain aktualisiert

---

## 🧪 Nach Deployment testen

1. **Gehe zu:** `https://buildwise.yourdomain.com/service-provider/buildwise-fees`
2. **Klicke:** "Jetzt bezahlen" bei einer offenen Rechnung
3. **Stripe Checkout:** Führe Test-Zahlung durch
4. **Erwartetes Ergebnis:**
   - ✅ Redirect zu: `https://buildwise.yourdomain.com/service-provider/buildwise-fees?payment=success&fee_id=X`
   - ✅ Success-Benachrichtigung erscheint
   - ✅ Status ändert sich zu "Bezahlt"
   - ✅ Webhook wird in Stripe Dashboard als "succeeded" angezeigt

---

## 🔍 Troubleshooting

### Problem: Webhook kommt nicht an
**Lösung:** Prüfe in Stripe Dashboard > Webhooks > Recent events ob Events gesendet werden

### Problem: Success URL ist falsch
**Lösung:** Prüfe ob `FRONTEND_URL` korrekt in render.com gesetzt ist

### Problem: CORS Fehler
**Lösung:** Füge Frontend-Domain zu `CORS_ORIGINS` hinzu

---

## 📚 Wichtige Links

- **Stripe Dashboard:** https://dashboard.stripe.com
- **render.com Dashboard:** https://dashboard.render.com
- **Stripe Webhooks Docs:** https://stripe.com/docs/webhooks
- **render.com Docs:** https://render.com/docs

---

## 💡 Lokale Entwicklung vs. Production

| Variable | Lokal | Production |
|----------|-------|------------|
| `FRONTEND_URL` | `http://localhost:5173` | `https://buildwise.yourdomain.com` |
| `STRIPE_SECRET_KEY` | `sk_test_xxx` | `sk_live_xxx` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_xxx` (Stripe CLI) | `whsec_xxx` (Stripe Dashboard) |
| `ENVIRONMENT_MODE` | `beta` | `production` |
| `BUILDWISE_FEE_PERCENTAGE` | `0.0` | `4.7` |
| `DATABASE_URL` | `sqlite:///./buildwise.db` | `postgresql://...` |

---

**Fertig! Mit dieser Konfiguration funktioniert alles automatisch auf jeder Domain! 🚀**

