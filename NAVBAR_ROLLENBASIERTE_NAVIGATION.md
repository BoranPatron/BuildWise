# Rollenbasierte Navbar-Navigation

## Übersicht

Die Navbar zeigt unterschiedliche Navigationselemente basierend auf der Benutzerrolle. Dienstleister sehen eine reduzierte Navigation mit nur "Dashboard" und "Gebühren", während Bauträger die vollständige Navigation erhalten.

## 🎯 Implementierung

### **Datei**: `Frontend/Frontend/src/components/Navbar.tsx`

## 👤 Dienstleister-Navigation

### **Sichtbare Elemente:**
- ✅ **Dashboard** - Link zu `/service-provider`
- ✅ **Gebühren** - Link zu `/service-provider/buildwise-fees`

### **Ausgeblendete Elemente:**
- ❌ **Übersicht** (Globale Projekte)
- ❌ **Favoriten** (Dropdown)
- ❌ **Pro** (Upgrade-Button)
- ❌ **Tools** (Dropdown)
- ❌ **"Neues Projekt"** (Mittiger Button)

### **Code-Implementierung:**
```typescript
{isServiceProvider() ? (
  /* Dienstleister-Navigation: nur Dashboard und Gebühren */
  <>
    <Link
      to="/service-provider"
      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300 ${
        isActive('/service-provider')
          ? 'bg-[#ffbd59] text-[#2c3539] font-semibold shadow-lg' 
          : 'text-white hover:bg-white/10 hover:text-[#ffbd59]'
      }`}
    >
      <Home size={18} />
      <span>Dashboard</span>
    </Link>

    <Link
      to="/service-provider/buildwise-fees"
      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300 ${
        isActive('/service-provider/buildwise-fees') 
          ? 'bg-[#ffbd59] text-[#2c3539] font-semibold shadow-lg' 
          : 'text-white hover:bg-white/10 hover:text-[#ffbd59]'
      }`}
    >
      <Euro size={18} />
      <span>Gebühren</span>
    </Link>
  </>
) : (
  /* Bauträger-Navigation: vollständige Navigation */
  // ... vollständige Navigation
)}
```

## 🏗️ Bauträger-Navigation

### **Sichtbare Elemente:**
- ✅ **Dashboard** - Link zu `/`
- ✅ **Übersicht** - Link zu `/global-projects`
- ✅ **Favoriten** - Dropdown mit konfigurierten Favoriten
- ✅ **Pro** - Upgrade-Button/Badge
- ✅ **Tools** - Dropdown (Dokumente, Visualisierung, Roadmap)
- ✅ **"Neues Projekt"** - Mittiger Button für Projekterstellung

### **Vollständige Navigation:**
```typescript
/* Bauträger-Navigation: vollständige Navigation */
<>
  <Link to="/">Dashboard</Link>
  <Link to="/global-projects">Übersicht</Link>
  <div className="relative group">Favoriten Dropdown</div>
  <Link to="/buildwise-fees">Pro</Link>
  <div className="relative group">Tools Dropdown</div>
</>
```

## 📱 Mobile Navigation

### **Dienstleister Mobile Menu:**
```typescript
{isServiceProvider() ? (
  /* Dienstleister Mobile Menu: nur Dashboard und Gebühren */
  <>
    <Link to="/service-provider">
      <Home size={18} />
      <span>Dashboard</span>
    </Link>
    
    <Link to="/service-provider/buildwise-fees">
      <Euro size={18} />
      <span>Gebühren</span>
    </Link>
  </>
) : (
  /* Bauträger Mobile Menu: vollständige Navigation */
  <>
    <Link to="/">Dashboard</Link>
    <Link to="/global-projects">Globale Übersicht</Link>
    <Link to="/tasks">Aufgaben</Link>
    <Link to="/finance">Finanzen</Link>
    <Link to="/documents">Dokumente</Link>
  </>
)}
```

## 🔧 Rollenprüfung

### **AuthContext Integration:**
```typescript
const { isServiceProvider } = useAuth();
```

### **Rolle-Erkennung:**
- **Dienstleister**: `user.user_role === 'service_provider'`
- **Bauträger**: `user.user_role === 'bautraeger'`

### **isServiceProvider() Funktion:**
```typescript
// In AuthContext
const isServiceProvider = () => {
  return user?.user_role === 'service_provider';
};
```

## 🎨 UI-Unterschiede

### **Layout-Anpassungen:**

#### **Dienstleister:**
- **Kompakte Navigation** - Nur 2 Hauptelemente
- **Kein mittiger Button** - "Neues Projekt" wird ausgeblendet
- **Vereinfachtes Layout** - Fokus auf wesentliche Funktionen

#### **Bauträger:**
- **Vollständige Navigation** - Alle verfügbaren Features
- **"Neues Projekt" Button** - Zentraler Erstellungsbutton
- **Dropdown-Menüs** - Favoriten und Tools

### **Styling:**
```typescript
// Aktiver Zustand
className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300 ${
  isActive(path)
    ? 'bg-[#ffbd59] text-[#2c3539] font-semibold shadow-lg' 
    : 'text-white hover:bg-white/10 hover:text-[#ffbd59]'
}`}
```

## 🚀 Features pro Rolle

### **Dienstleister:**
| Feature | Verfügbar | Route |
|---------|-----------|-------|
| Dashboard | ✅ | `/service-provider` |
| Gebühren | ✅ | `/service-provider/buildwise-fees` |
| Geo-Search | ✅ | In Dashboard integriert |
| Angebotserstellung | ✅ | In Dashboard integriert |

### **Bauträger:**
| Feature | Verfügbar | Route |
|---------|-----------|-------|
| Dashboard | ✅ | `/` |
| Globale Übersicht | ✅ | `/global-projects` |
| Favoriten | ✅ | Dropdown |
| Pro-Features | ✅ | `/buildwise-fees` |
| Tools | ✅ | Dropdown |
| Projekterstellung | ✅ | Modal |
| Dokumente | ✅ | `/documents` |
| Visualisierung | ✅ | `/visualize` |
| Roadmap | ✅ | `/roadmap` |

## 🔒 Sicherheit

### **Route-Schutz:**
- Alle Routes sind durch JWT-Authentifizierung geschützt
- Rollenbasierte Zugriffskontrolle im Backend
- Frontend zeigt nur erlaubte Navigation

### **Backend-Validierung:**
```python
# Beispiel Backend-Schutz
@router.get("/service-provider/buildwise-fees")
async def get_service_provider_fees(
    current_user: User = Depends(get_current_user)
):
    if current_user.user_role != "service_provider":
        raise HTTPException(status_code=403, detail="Access denied")
    # ...
```

## 📊 Navigation-Matrix

| Element | Dienstleister | Bauträger | Mobile |
|---------|---------------|-----------|--------|
| Dashboard | ✅ | ✅ | ✅ |
| Gebühren | ✅ | ✅ | ✅ |
| Übersicht | ❌ | ✅ | ✅ |
| Favoriten | ❌ | ✅ | ❌ |
| Pro | ❌ | ✅ | ❌ |
| Tools | ❌ | ✅ | ❌ |
| Neues Projekt | ❌ | ✅ | ❌ |

## 🎯 Benutzerfreundlichkeit

### **Dienstleister-UX:**
- **Fokussierte Navigation** - Keine Ablenkung durch irrelevante Features
- **Schneller Zugriff** - Direkte Links zu wichtigsten Funktionen
- **Klare Struktur** - Dashboard für Hauptfunktionen, Gebühren für Finanzen

### **Bauträger-UX:**
- **Vollständige Kontrolle** - Zugriff auf alle Platform-Features
- **Effiziente Navigation** - Dropdown-Menüs für verwandte Funktionen
- **Schnelle Projekterstellung** - Prominenter "Neues Projekt" Button

## ✅ Status: Vollständig implementiert

Die rollenbasierte Navigation ist vollständig implementiert:
- ✅ **Dienstleister sehen nur Dashboard und Gebühren**
- ✅ **Bauträger sehen vollständige Navigation**
- ✅ **Mobile Navigation entsprechend angepasst**
- ✅ **Konsistente Styling und UX** 