# 🧪 Stripe Payment Test - Schritt für Schritt

## Problem-Diagnose

Du landest auf der Startseite `/service-provider` statt auf `/service-provider/buildwise-fees`.

### Mögliche Ursachen:
1. ❌ Backend leitet zur falschen URL weiter
2. ❌ Frontend Hot-Reload hat die Änderungen nicht übernommen
3. ❌ Browser-Cache zeigt alte Version

---

## 🔍 Schritt 1: Backend-Konfiguration prüfen

Öffne die Backend-Konsole und suche nach:
```
[Stripe] Checkout Session erstellt
```

**Erwartete URL in den Logs:**
```
success_url: http://localhost:5173/service-provider/buildwise-fees?payment=success&fee_id=X
```

**Falls falsch:** Backend neu starten!

---

## 🔍 Schritt 2: Frontend prüfen

### A) Browser-Konsole öffnen (F12)

Nach der Zahlung solltest du in der Konsole sehen:
```
🔍 URL Parameter: { paymentStatus: 'success', feeIdParam: '1' }
✅ Zahlung erfolgreich erkannt!
```

**Falls nicht:** Frontend neu starten und Browser-Cache leeren (Strg+Shift+R)

### B) URL manuell testen

Gehe direkt zu dieser URL:
```
http://localhost:5173/service-provider/buildwise-fees?payment=success&fee_id=1
```

**Erwartetes Ergebnis:**
- ✅ Du siehst die BuildWise Fees Seite
- ✅ Große grüne Success-Box erscheint oben
- ✅ Text: "🎉 Zahlung erfolgreich! Gebühr #1 wurde bezahlt."

**Falls nicht sichtbar:** Frontend hat die Änderungen nicht geladen!

---

## 🔄 Schritt 3: Alles neu starten (Hard Reset)

### 1. Backend stoppen
```bash
Strg+C im Backend-Terminal
```

### 2. Frontend stoppen
```bash
Strg+C im Frontend-Terminal
```

### 3. Browser-Cache leeren
- Chrome: `Strg+Shift+Delete` → "Cached images and files" → Clear
- Oder: `Strg+Shift+R` (Hard Reload)

### 4. Backend neu starten
```bash
cd C:\Users\user\Documents\04_Repo\BuildWise
python .\start_backend.py
```

**Warte bis du siehst:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 5. Frontend neu starten
```bash
cd C:\Users\user\Documents\04_Repo\Frontend\Frontend
npm run dev
```

**Warte bis du siehst:**
```
  VITE v... ready in ...ms
  ➜  Local:   http://localhost:5173/
```

### 6. Stripe CLI läuft?
Prüfe ob das Stripe CLI Terminal noch läuft:
```bash
stripe listen --forward-to localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

**Sollte zeigen:**
```
> Ready! You are using Stripe API Version [...]
  Your webhook signing secret is whsec_...
```

---

## 🧪 Schritt 4: Test durchführen

### A) Manuelle URL-Test (ZUERST!)

1. **Öffne Browser (Neuer Tab):**
   ```
   http://localhost:5173/service-provider/buildwise-fees?payment=success&fee_id=1
   ```

2. **Öffne Browser-Konsole (F12)**

3. **Erwartetes Ergebnis:**
   - ✅ Konsole zeigt: `🔍 URL Parameter: { paymentStatus: 'success', feeIdParam: '1' }`
   - ✅ Konsole zeigt: `✅ Zahlung erfolgreich erkannt!`
   - ✅ **GROSSE GRÜNE BOX** oben auf der Seite
   - ✅ Text: "🎉 Zahlung erfolgreich! Gebühr #1 wurde bezahlt."

**Falls du die Box NICHT siehst → Frontend hat die Änderungen nicht!**

### B) Stripe Payment Test (DANACH!)

Nur wenn der manuelle URL-Test funktioniert:

1. **Gehe zu:** http://localhost:5173/service-provider/buildwise-fees
2. **Klicke:** "Jetzt bezahlen" bei einer offenen Rechnung
3. **Stripe Checkout öffnet sich**
4. **Verwende Testkarte:** `4242 4242 4242 4242`
5. **Ablaufdatum:** Beliebig in der Zukunft (z.B. `12/34`)
6. **CVC:** Beliebig (z.B. `123`)
7. **Klicke:** "Bezahlen"

### C) Beobachte die Terminals

**Stripe CLI Terminal sollte zeigen:**
```
--> checkout.session.completed [evt_xxx]
<-- [200] POST http://localhost:8000/api/v1/buildwise-fees/stripe-webhook
```

**Backend Terminal sollte zeigen:**
```
[Webhook] ✅ Stripe Webhook erhalten
[Webhook] ✅ Gebühr X erfolgreich als bezahlt markiert
```

**Browser sollte:**
- Weiterleiten zu: `http://localhost:5173/service-provider/buildwise-fees?payment=success&fee_id=X`
- **GROSSE GRÜNE SUCCESS-BOX** zeigen
- Status der Gebühr auf "Bezahlt" (grün) ändern

---

## ❌ Troubleshooting

### Problem: Ich lande auf `/service-provider` (Startseite)

**Ursache:** Stripe leitet zur falschen URL weiter

**Lösung:**
1. Öffne: `app/core/config.py`
2. Prüfe Zeile ~52: `frontend_url: str = "http://localhost:5173"`
3. Prüfe Zeilen ~54-62: Die `@property` Funktionen
4. Backend neu starten!

### Problem: Keine Success-Box sichtbar

**Ursache:** Frontend hat die Änderungen nicht geladen

**Lösung:**
1. Frontend stoppen (Strg+C)
2. Node modules neu bauen (falls nötig): `npm install`
3. Frontend neu starten: `npm run dev`
4. Browser-Cache leeren: `Strg+Shift+R`
5. Manuellen URL-Test durchführen (siehe oben)

### Problem: Webhook kommt nicht an

**Ursache:** Stripe CLI läuft nicht oder Backend ist gestoppt

**Lösung:**
1. Prüfe ob Stripe CLI läuft (separates Terminal)
2. Prüfe ob Backend auf Port 8000 läuft
3. Prüfe `stripe_webhook_secret` in `config.py`

### Problem: Status ändert sich nicht zu "Bezahlt"

**Ursache:** Webhook funktioniert nicht

**Lösung:**
1. Prüfe Stripe CLI Terminal auf Fehler
2. Prüfe Backend Terminal auf Webhook-Logs
3. Prüfe `stripe_webhook_secret` ist korrekt gesetzt
4. Backend neu starten nach Secret-Änderung

---

## ✅ Checkliste

Vor dem Test prüfen:

- [ ] Backend läuft auf Port 8000
- [ ] Frontend läuft auf Port 5173
- [ ] Stripe CLI läuft (`stripe listen ...`)
- [ ] Browser-Cache geleert (Strg+Shift+R)
- [ ] Manueller URL-Test erfolgreich
- [ ] Browser-Konsole (F12) ist offen zum Debuggen

---

## 📞 Debug-Hilfe

Wenn gar nichts funktioniert, führe das aus und schicke mir die Ausgabe:

```bash
# Backend-Konfiguration prüfen
cd C:\Users\user\Documents\04_Repo\BuildWise
python -c "from app.core.config import settings; print(f'Frontend URL: {settings.frontend_url}'); print(f'Success URL: {settings.stripe_payment_success_url}'); print(f'Cancel URL: {settings.stripe_payment_cancel_url}')"
```

**Erwartete Ausgabe:**
```
Frontend URL: http://localhost:5173
Success URL: http://localhost:5173/service-provider/buildwise-fees?payment=success
Cancel URL: http://localhost:5173/service-provider/buildwise-fees?payment=cancelled
```

---

**Viel Erfolg! 🚀**


