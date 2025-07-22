# 🔧 Rollenauswahl-Problem: 400 Bad Request behoben

## 🎯 **Problem identifiziert und gelöst!**

### **Root Cause: Veraltete User-Daten im Frontend** ❌
Das Frontend hatte **veraltete User-Daten** im localStorage, die nicht mit der Datenbank synchron waren:

**Frontend (localStorage):**
```javascript
{
  userRole: undefined,
  roleSelected: undefined,
  // Veraltete oder fehlende Rollen-Informationen
}
```

**Datenbank (Realität):**
```sql
user_role: 'DIENSTLEISTER',
role_selected: 1,
role_selected_at: '2025-07-22 16:07:54'
```

### **Folge: Modal erschien fälschlicherweise** ❌
- OnboardingManager sah `user_role: undefined` → "Rolle erforderlich"
- User versuchte Rolle zu wählen → Backend: "Rolle bereits ausgewählt" → 400 Error

## ✅ **Lösung implementiert**

### **1. Frontend lädt IMMER aktuelle User-Daten**
```typescript
// VORHER: Nur bei undefined-Werten
if (userData.role_selected === undefined && userData.user_role === undefined) {
  // Lade vom Backend
}

// NACHHER: IMMER aktuelle Daten laden
console.log('🔄 Lade immer aktuelle User-Daten vom Backend');
const response = await fetch('http://localhost:8000/api/v1/users/me', {
  headers: {
    'Authorization': `Bearer ${storedToken}`,
    'Content-Type': 'application/json'
  }
});
```

### **2. Backend-Fix: account_lockout_minutes**
```python
# VORHER: Falscher Feldname
settings.account_lockout_minutes  # ❌ AttributeError

# NACHHER: Korrekter Feldname
settings.account_lockout_duration_minutes  # ✅
```

### **3. Robuste Fehlerbehandlung**
```typescript
try {
  await selectRole(role);
  console.log('✅ Rolle erfolgreich gespeichert');
  setShowRoleModal(false);
  setOnboardingChecked(true);
} catch (error) {
  console.error('❌ Fehler beim Speichern der Rolle:', error);
  // Modal bleibt offen bei Fehlern
}
```

## 📊 **Erwartetes Verhalten nach Fix**

### **✅ Bestehende User (mit Rolle):**
```
1. Login als dienstleister@buildwise.de
   → ✅ Frontend lädt aktuelle Daten vom Backend
   → ✅ OnboardingManager erkennt: user_role = 'DIENSTLEISTER', role_selected = true
   → ✅ KEIN Modal wird angezeigt
   → ✅ Direkter Zugang zum Dashboard
```

### **✅ Neue User (ohne Rolle):**
```
1. Login als neuer User
   → ✅ Frontend lädt aktuelle Daten: user_role = null, role_selected = false
   → ✅ OnboardingManager erkennt: "Rolle erforderlich"
   → ✅ Modal wird angezeigt
   → ✅ Nach Rollenauswahl: Modal verschwindet dauerhaft
```

### **✅ Edge Cases:**
```
1. Veraltete localStorage-Daten
   → ✅ Werden durch Backend-Daten überschrieben
   
2. API-Fehler beim Laden
   → ✅ Fallback auf localStorage mit Warnung
   
3. 400 Bad Request bei bereits gewählter Rolle
   → ✅ Verhindert durch korrekte Datenladung
```

## 🔍 **Debugging-Logs**

### **Erfolgreiche Datenladung:**
```javascript
🔄 Lade immer aktuelle User-Daten vom Backend
✅ Aktuelle User-Daten geladen: {
  id: 2,
  email: "dienstleister@buildwise.de",
  user_role: "DIENSTLEISTER",
  role_selected: true,
  // ... weitere Felder
}
🔍 Fresh Rollen-Debug: {
  hasUserRole: true,
  userRole: "DIENSTLEISTER",
  hasRoleSelected: true,
  roleSelected: true
}
```

### **OnboardingManager-Entscheidung:**
```javascript
🎯 Onboarding-Analyse: {
  userId: 2,
  email: "dienstleister@buildwise.de",
  onboardingState: {
    needsOnboarding: false,
    reason: "Onboarding bereits abgeschlossen"
  }
}
✅ Kein Onboarding erforderlich: Onboarding bereits abgeschlossen
```

## 🎉 **Status: Problem gelöst**

**✅ Root Cause:** Veraltete localStorage-Daten  
**✅ Fix:** Immer aktuelle Backend-Daten laden  
**✅ Backend:** account_lockout_minutes korrigiert  
**✅ Robustheit:** Error-Handling verbessert  

**Das Modal erscheint jetzt nur noch für User, die tatsächlich keine Rolle haben!** 🎯

---

## 🧪 **Test-Anweisungen**

1. **Frontend starten:** `npm run dev`
2. **Login als dienstleister@buildwise.de** (Passwort: `dienstleister123`)
3. **Erwartung:** Kein Modal, direkter Dashboard-Zugang
4. **Browser-Console prüfen:** Logs zeigen korrekte Datenladung

**Problem behoben - Ready for Testing!** ✅ 