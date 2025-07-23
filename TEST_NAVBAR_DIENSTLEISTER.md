# Test: Dienstleister-Navbar

## 🧪 Testanleitung

### **Schritt 1: Login als Dienstleister**
1. Öffne `http://localhost:3000`
2. Logge dich mit OAuth Google ein
3. Wähle Rolle: **Dienstleister**

### **Schritt 2: Navbar-Überprüfung**
**Erwartete Navigation (sollte nur 2 Elemente zeigen):**
- ✅ **Dashboard** - Link zu `/service-provider`
- ✅ **Gebühren** - Link zu `/service-provider/buildwise-fees`

**Nicht sichtbar (sollten ausgeblendet sein):**
- ❌ **Übersicht** (Globale Projekte)
- ❌ **Favoriten** (Dropdown)
- ❌ **Pro** (Upgrade-Button)
- ❌ **Tools** (Dropdown)
- ❌ **"Neues Projekt"** (Mittiger Button)

### **Schritt 3: Debug-Überprüfung**
Öffne die Browser-Konsole (F12) und prüfe:

```javascript
// Erwartete Debug-Logs:
🔍 isServiceProvider Check: {
  user_type: "private",
  user_role: "DIENSTLEISTER", // Großbuchstaben vom Backend
  email: "your-email@gmail.com",
  result: true
}
```

### **Schritt 4: Funktionalität testen**
1. **Dashboard-Link**: Sollte zu `/service-provider` führen
2. **Gebühren-Link**: Sollte zu `/service-provider/buildwise-fees` führen
3. **Mobile Menu**: Sollte auch nur Dashboard und Gebühren zeigen

## 🔧 Erwartete isServiceProvider() Logik

```typescript
const isServiceProvider = () => {
  const result = user?.user_role === 'dienstleister' ||  // Kleinbuchstaben (Frontend)
                 user?.user_role === 'DIENSTLEISTER' ||  // Großbuchstaben (Backend)
                 user?.user_type === 'service_provider' || 
                 user?.email?.includes('dienstleister');
  
  return result; // Sollte TRUE zurückgeben
};
```

## 🐛 Bekannte Probleme

### **Problem**: Debug zeigt `User Role: dienstleister` aber Backend hat `DIENSTLEISTER`
**Ursache**: Enum-Werte werden unterschiedlich serialisiert
**Lösung**: AuthContext prüft beide Varianten (Groß- und Kleinbuchstaben)

### **Problem**: Navbar zeigt falsche Navigation
**Ursache**: `isServiceProvider()` erkennt Rolle nicht korrekt
**Lösung**: Erweiterte Rollenerkennung implementiert

## ✅ Erfolgskriterien

- [ ] Nur 2 Navigation-Elemente sichtbar
- [ ] Dashboard-Link funktioniert
- [ ] Gebühren-Link funktioniert
- [ ] Mobile Menu zeigt korrekte Navigation
- [ ] Console-Log zeigt `result: true`
- [ ] Kein "Neues Projekt" Button sichtbar
- [ ] Keine Favoriten/Pro/Tools Dropdowns sichtbar

## 🔄 Nächste Schritte bei Fehlern

1. **Browser-Cache leeren** (Strg+F5)
2. **Console-Logs prüfen** auf Fehler
3. **AuthContext Debug** aktivieren
4. **Backend-Antwort prüfen** in Network-Tab
5. **Lokalen Storage prüfen** auf veraltete Daten 