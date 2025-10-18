# 🚀 Stripe Webhook Setup - Quick Start

## Status: ✅ Stripe CLI installiert!

## Nächste Schritte (MANUELL):

### 1. Stripe Login
```bash
stripe login
```

### 2. Webhook Forwarding (NEUES Terminal)
```bash
cd C:\Users\user\Documents\04_Repo\BuildWise
stripe listen --forward-to localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

### 3. Secret kopieren & eintragen
- Kopiere das `whsec_xxx` Secret aus dem Terminal
- Füge es in `app/core/config.py` Zeile 48 ein
- Backend neu starten

## Vollständige Anleitung
Siehe: `STRIPE_SETUP_FERTIG.md`

