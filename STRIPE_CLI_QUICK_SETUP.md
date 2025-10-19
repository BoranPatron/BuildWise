# 🚀 Stripe CLI - 5 Minuten Setup

## Warum brauchst du das?

**Ohne Stripe CLI/Webhook:**
- ❌ Status bleibt auf "open"
- ❌ Keine automatische Bestätigung
- ❌ Manuelle Markierung erforderlich

**Mit Stripe CLI/Webhook:**
- ✅ Status wird automatisch auf "paid" gesetzt
- ✅ Sofortige Bestätigung
- ✅ Professional wie in Production

## 🛠️ Installation (Windows)

### Option 1: Chocolatey (Empfohlen)
```powershell
# Als Administrator ausführen
choco install stripe-cli
```

### Option 2: Manueller Download
1. Gehe zu: https://github.com/stripe/stripe-cli/releases/latest
2. Downloade: `stripe_X.X.X_windows_x86_64.zip`
3. Entpacke in `C:\stripe\`
4. Füge zu PATH hinzu

## 📝 Setup (3 Schritte)

### Schritt 1: Login
```bash
stripe login
```
- Browser öffnet sich
- Bei Stripe einloggen
- Zugriff erlauben

### Schritt 2: Webhook forwarding starten

**Öffne ein NEUES Terminal** (parallel zum Backend & Frontend):

```bash
stripe listen --forward-to localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

**Output:**
```
> Ready! You are using Stripe API Version [2024-04-10]. Your webhook signing secret is whsec_xxx (^C to quit)
```

### Schritt 3: Secret kopieren

Kopiere das `whsec_xxx` Secret und füge es in `app/core/config.py` ein:

```python
stripe_webhook_secret: str = "whsec_IHR_SECRET_HIER"
```

### Schritt 4: Backend neu starten

```bash
# Im Backend-Terminal:
Ctrl+C
python .\start_backend.py
```

## ✅ Fertig!

Jetzt testen:

1. **Stripe-Zahlung durchführen**
2. **Im Stripe CLI Terminal siehst du:**
   ```
   --> checkout.session.completed [evt_xxx]
   <-- [200] POST http://localhost:8000/api/v1/buildwise-fees/stripe-webhook
   ```
3. **Im Backend-Terminal siehst du:**
   ```
   [Webhook] Stripe Webhook erhalten
   [Webhook] ✅ Gebühr 1 erfolgreich als bezahlt markiert
   ```
4. **Im Frontend:**
   - Status ändert sich zu "Bezahlt" (grün) ✅
   - Success-Seite zeigt Bestätigung ✅

## 🔧 Alternative: Manuell markieren (ohne Webhook)

Falls du Stripe CLI nicht installieren möchtest:

1. Nach Zahlung auf BuildWise Fees Seite gehen
2. Grüner Haken-Button klicken: "Als bezahlt markieren"
3. Status wird manuell auf "paid" gesetzt

Aber das ist nicht professionell - Webhooks sind Best Practice!

## 📊 Terminals Übersicht

Du solltest jetzt **3 Terminals** offen haben:

```
Terminal 1: Backend
> python .\start_backend.py

Terminal 2: Frontend  
> npm run dev

Terminal 3: Stripe CLI (NEU!)
> stripe listen --forward-to localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

## 🎉 Fertig!

Mit dieser Setup funktioniert alles wie in Production!

