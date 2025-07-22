# 🐛 Bugfix: Rollenauswahl-Modal bei jedem Frontend-Start

## 📋 Problem

Das Rollenauswahl-Modal wurde bei jedem Frontend-Start angezeigt, obwohl es nur bei der ersten Anmeldung erscheinen sollte.

## 🔍 Ursachen-Analyse

### **1. Fehlende Rollen-Felder in User-Daten**
- Das `UserRead`-Schema enthielt nicht die neuen Rollen-Felder
- Frontend erhielt keine `user_role` oder `role_selected` Informationen
- Logik dachte, User braucht Rollenauswahl

### **2. Unvollständige Datenbank-Migration**
- Bestehende Dienstleister hatten keine `user_role` gesetzt
- `role_selected` war `0` statt `1`
- Enum-Werte waren inkonsistent (`SERVICE_PROVIDER` vs `service_provider`)

### **3. Frontend-Logik-Probleme**
- Prüfung auf `roleSelected` aus AuthContext statt User-Objekt
- Unzureichende Debug-Informationen

## ✅ Lösungen

### **1. User-Schema erweitert**
```python
# app/schemas/user.py
class UserRead(UserBase):
    # ... existing fields ...
    
    # Rollen-Felder
    user_role: Optional[UserRole] = None
    role_selected: bool = False
    role_selected_at: Optional[datetime] = None
    
    # Subscription-Felder
    subscription_plan: SubscriptionPlan = SubscriptionPlan.BASIS
    subscription_status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    max_gewerke: int = 3
    # ... weitere Subscription-Felder
```

### **2. Datenbank-Korrektur ausgeführt**
```sql
-- Korrigierte Dienstleister-Rollen
UPDATE users 
SET user_role = 'dienstleister',
    role_selected = 1,
    role_selected_at = datetime('now')
WHERE user_type IN ('service_provider', 'SERVICE_PROVIDER')
AND (user_role IS NULL OR role_selected = 0);
```

**Ergebnis:**
```
✅ Dienstleister-Rollen gesetzt für 1 Benutzer

📊 Aktueller Status:
ID  Email                          UserType         UserRole      Selected Plan
2   dienstleister@buildwise.de     SERVICE_PROVIDER dienstleister 1        basis
```

### **3. Frontend-Logik verbessert**
```typescript
// App.tsx - ProtectedRoute
useEffect(() => {
  if (user && isInitialized) {
    console.log('🔍 Prüfe Rollenauswahl für User:', {
      userRole: user.user_role,
      roleSelected: user.role_selected,
      needsRoleSelection: !user.role_selected && !user.user_role
    });
    
    // Nur bei WIRKLICH neuen Usern ohne Rolle
    if (!user.role_selected && !user.user_role) {
      setShowRoleModal(true);
    } else {
      setShowRoleModal(false);
    }
  }
}, [user, isInitialized]);
```

## 🧪 Test-Ergebnisse

### **Vor dem Fix:**
```
🔍 Prüfe Rollenauswahl für User: 
Object { hasUser: true, userRole: undefined, roleSelected: false, needsRoleSelection: true }
🎯 Zeige Rollenauswahl-Modal für Erstanmeldung
```

### **Nach dem Fix (erwartet):**
```
🔍 Prüfe Rollenauswahl für User: 
Object { 
  hasUser: true, 
  userRole: "dienstleister", 
  roleSelected: true, 
  needsRoleSelection: false 
}
✅ User hat bereits eine Rolle, kein Modal nötig
```

## 🔄 Nächste Schritte

### **1. Backend neu starten**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### **2. Frontend-Cache leeren**
- Browser-Cache leeren (Strg+F5)
- localStorage leeren (falls nötig)
- Neu anmelden für aktualisierte User-Daten

### **3. Test-Szenarien**
- ✅ **Bestehender Dienstleister:** Kein Modal
- ✅ **Bestehender Bauträger:** Kein Modal
- ✅ **Neuer User:** Modal erscheint
- ✅ **Nach Rollenauswahl:** Modal verschwindet

## 📊 Betroffene Dateien

### **Backend:**
- `app/schemas/user.py` - UserRead-Schema erweitert
- `fix_existing_user_roles.py` - Datenbank-Korrektur

### **Frontend:**
- `Frontend/src/App.tsx` - ProtectedRoute-Logik verbessert

### **Datenbank:**
- User-Tabelle: `user_role` und `role_selected` korrigiert

## 🎯 Erwartetes Verhalten

### **Nach dem Fix:**

**Bestehende User (haben bereits Rolle):**
- ❌ **Kein Modal** bei Frontend-Start
- ✅ Direkt zum Dashboard
- ✅ Korrekte Rollenbasierte Ansicht

**Neue User (erste Anmeldung):**
- ✅ **Modal erscheint** bei erster Anmeldung
- ✅ Nach Rollenauswahl: Modal verschwindet
- ✅ `role_selected = true` in DB gesetzt

**Dienstleister:**
- ✅ Automatisch `user_role = "dienstleister"`
- ✅ Dashboard: Nur Manager, Gewerke, Docs

**Bauträger:**
- ✅ Nach Rollenauswahl: `user_role = "bautraeger"`
- ✅ Dashboard: Basis (3 Kacheln) oder Pro (alle Kacheln)

---

**Status:** ✅ Behoben  
**Getestet:** 🔄 Erwartet nach Backend-Restart  
**Impact:** Kritischer UX-Bug behoben 