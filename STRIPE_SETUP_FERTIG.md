# ✅ Stripe CLI Setup - Fertig!

## 🎉 Was wurde gemacht:

1. ✅ **Stripe CLI installiert** (v1.21.8)
2. ✅ **PATH konfiguriert** 
3. ✅ **Stripe CLI funktioniert**

---

## 🚀 Nächste Schritte (MANUELL):

### Schritt 1: Stripe Login

Öffne ein **NEUES PowerShell-Terminal** und führe aus:

```bash
stripe login
```

**Was passiert:**
- Ein Browser-Fenster öffnet sich
- Du wirst zu Stripe weitergeleitet
- Logge dich mit deinem Stripe-Account ein
- Erlaube den Zugriff für Stripe CLI

---

### Schritt 2: Webhook Forwarding starten

**WICHTIG:** Öffne ein **NEUES Terminal-Fenster** (parallel zu Backend & Frontend)

```bash
cd C:\Users\user\Documents\04_Repo\BuildWise
stripe listen --forward-to localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

**Was passiert:**
- Stripe CLI startet
- Es zeigt: `Your webhook signing secret is whsec_xxxxxxxxxxxxx`
- **KOPIERE** das gesamte `whsec_xxxxxxxxxxxxx` Secret!

Beispiel Output:
```
> Ready! You are using Stripe API Version [2024-04-10]. 
  Your webhook signing secret is whsec_abc123xyz456 (^C to quit)
```

---

### Schritt 3: Webhook Secret in config.py eintragen

Öffne die Datei: `app/core/config.py` (Zeile 48)

**VORHER:**
```python
stripe_webhook_secret: str = ""  # Wird nach Webhook-Erstellung gesetzt
```

**NACHHER (Beispiel):**
```python
stripe_webhook_secret: str = "whsec_abc123xyz456"  # Dein kopiertes Secret
```

---

### Schritt 4: Backend neu starten

Im **Backend-Terminal**:

```bash
# Strg+C (Backend stoppen)
python .\start_backend.py
```

---

## ✅ Fertig! Jetzt testen:

### Terminal-Übersicht (du solltest 3 Terminals haben):

```
📍 Terminal 1: Backend
   > cd C:\Users\user\Documents\04_Repo\BuildWise
   > python .\start_backend.py

📍 Terminal 2: Frontend  
   > cd C:\Users\user\Documents\04_Repo\Frontend\Frontend
   > npm run dev

📍 Terminal 3: Stripe CLI (NEU!)
   > cd C:\Users\user\Documents\04_Repo\BuildWise
   > stripe listen --forward-to localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

---

### Test durchführen:

1. **Gehe zu:** http://localhost:5173/buildwise-fees
2. **Klicke:** "Jetzt bezahlen" bei einer offenen Rechnung
3. **Stripe Checkout:** Verwende Testkarte `4242 4242 4242 4242`
4. **Beobachte die Terminals:**

**Im Stripe CLI Terminal siehst du:**
```
--> checkout.session.completed [evt_xxx]
<-- [200] POST http://localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

**Im Backend Terminal siehst du:**
```
[Webhook] ✅ Stripe Webhook erhalten
[Webhook] ✅ Gebühr 1 erfolgreich als bezahlt markiert
```

**Im Browser:**
- ✅ Du wirst zu `/buildwise-fees?payment=success&fee_id=1` weitergeleitet
- ✅ Status ist jetzt "Bezahlt" (grün)
- ✅ Erfolgs-Nachricht wird angezeigt

---

## 🔧 Troubleshooting

### Problem: "stripe: command not found"
**Lösung:** Öffne ein **NEUES** PowerShell-Fenster (PATH muss neu geladen werden)

### Problem: Webhook kommt nicht an
**Lösung:** 
- Prüfe ob Stripe CLI läuft (`stripe listen ...`)
- Prüfe ob Backend läuft (Port 8000)
- Prüfe ob `stripe_webhook_secret` in `config.py` gesetzt ist

### Problem: Status ändert sich nicht
**Lösung:**
- Backend neu starten (nach Secret-Update)
- Browser-Seite neu laden (F5)

---

## 📊 Wie es funktioniert:

```
1. User klickt "Jetzt bezahlen"
   ↓
2. Frontend: Öffnet Stripe Checkout
   ↓
3. User zahlt mit Testkarte
   ↓
4. Stripe sendet Event → Stripe CLI
   ↓
5. Stripe CLI forwarded Event → Backend Webhook
   ↓
6. Backend: Markiert Rechnung als "paid"
   ↓
7. Frontend: Lädt Status neu und zeigt "Bezahlt" ✅
```

---

## 🎉 Fertig!

Jetzt funktioniert alles automatisch wie in Production!

Keine manuellen Markierungen mehr nötig. 🚀


