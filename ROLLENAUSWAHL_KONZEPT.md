# 🏗️ Rollenauswahl bei Erstanmeldung - Konzept

## 📋 Übersicht

**Ziel:** Bei der ersten Anmeldung soll der Benutzer seine Rolle wählen können (Bauträger/Bauherr oder Dienstleister), die dann seine Ansicht und Berechtigungen in der Anwendung bestimmt.

## 🎯 Anforderungen

### 1. **Rollenauswahl-Dialog**
- Erscheint nur bei der ersten Anmeldung
- Zwei Optionen: "Bauträger/Bauherr" oder "Dienstleister"
- Modal/Dialog kann nicht übersprungen werden
- Benutzerfreundliches Design mit Icons

### 2. **Rollenzuweisung**
- **Bauträger/Bauherr:** 
  - Sieht die komplette Bauträger-Ansicht
  - Zugriff auf alle Funktionen
  
- **Dienstleister:**
  - Sieht nur die Dienstleister-Ansicht
  - Eingeschränkte Dashboard-Kacheln: nur "Manager", "Gewerk" und "Docs"

### 3. **Technische Anforderungen**
- Rolle wird in der Datenbank gespeichert
- Rolle kann später vom Admin geändert werden
- OAuth-Benutzer bekommen auch die Rollenauswahl

## 🏗️ Architektur-Design

### **Backend-Änderungen:**

1. **User Model erweitern:**
```python
class User(Base):
    # Existing fields...
    user_role = Column(Enum(UserRole), nullable=True)  # Neu
    role_selected = Column(Boolean, default=False)  # Neu
    role_selected_at = Column(DateTime, nullable=True)  # Neu
```

2. **UserRole Enum:**
```python
class UserRole(str, Enum):
    BAUTRAEGER = "bautraeger"  # Bauträger/Bauherr
    DIENSTLEISTER = "dienstleister"  # Dienstleister
    ADMIN = "admin"  # Admin (kann alles)
```

3. **API Endpoints:**
- `GET /api/v1/auth/check-role` - Prüft ob Rolle ausgewählt wurde
- `POST /api/v1/auth/select-role` - Speichert die gewählte Rolle

### **Frontend-Änderungen:**

1. **RoleSelectionModal Component:**
- Modal-Dialog mit zwei Karten zur Auswahl
- Icons und Beschreibungen für jede Rolle
- Bestätigungs-Button

2. **AuthContext erweitern:**
- `userRole` State hinzufügen
- `roleSelected` State hinzufügen
- `selectRole()` Funktion hinzufügen

3. **Dashboard-Filterung:**
- Kacheln basierend auf Benutzerrolle filtern
- Dienstleister sehen nur: "Manager", "Gewerk", "Docs"

## 🔄 User Flow

### **Erstanmeldung:**
1. Benutzer meldet sich an (OAuth oder E-Mail)
2. System prüft `role_selected` Flag
3. Wenn `false` → RoleSelectionModal wird angezeigt
4. Benutzer wählt Rolle
5. Rolle wird gespeichert, `role_selected = true`
6. Weiterleitung zum Dashboard mit gefilterten Kacheln

### **Wiederkehrende Anmeldung:**
1. Benutzer meldet sich an
2. System prüft `role_selected` Flag
3. Wenn `true` → Direkte Weiterleitung zum Dashboard
4. Dashboard zeigt Kacheln basierend auf `user_role`

## 🎨 UI/UX Design

### **RoleSelectionModal:**

```
┌─────────────────────────────────────────────┐
│          Willkommen bei BuildWise!          │
│                                             │
│    Bitte wählen Sie Ihre Rolle aus:        │
│                                             │
│  ┌─────────────┐      ┌─────────────┐      │
│  │   🏗️        │      │    🔧       │      │
│  │             │      │             │      │
│  │ Bauträger/  │      │Dienstleister│      │
│  │  Bauherr    │      │             │      │
│  │             │      │             │      │
│  │ Projekte    │      │  Angebote   │      │
│  │ verwalten   │      │ erstellen   │      │
│  └─────────────┘      └─────────────┘      │
│                                             │
│         Diese Auswahl kann später           │
│         vom Admin geändert werden           │
└─────────────────────────────────────────────┘
```

### **Dashboard-Kacheln für Dienstleister:**

Nur diese Kacheln werden angezeigt:
- **Manager** - Verwaltung von Angeboten/Aufträgen
- **Gewerk** - Gewerk-spezifische Funktionen
- **Docs** - Dokumentenverwaltung

## 🔒 Sicherheit & Berechtigungen

### **Backend-Validierung:**
1. Jeder API-Endpoint prüft die Benutzerrolle
2. Rollenbasierte Zugriffskontrolle (RBAC)
3. Middleware für Rollenprüfung

### **Frontend-Schutz:**
1. Route Guards basierend auf Rolle
2. Komponenten-Sichtbarkeit basierend auf Rolle
3. API-Calls nur für berechtigte Funktionen

## 📊 Datenbank-Schema

### **User Table Erweiterungen:**
```sql
ALTER TABLE users ADD COLUMN user_role VARCHAR(20);
ALTER TABLE users ADD COLUMN role_selected BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN role_selected_at TIMESTAMP;

-- Index für Performance
CREATE INDEX idx_users_role ON users(user_role);
```

## 🧪 Test-Szenarien

1. **Neue Benutzer-Registrierung:**
   - E-Mail-Registrierung → Rollenauswahl
   - OAuth-Registrierung → Rollenauswahl

2. **Rollenbasierte Ansichten:**
   - Bauträger → Alle Kacheln sichtbar
   - Dienstleister → Nur 3 Kacheln sichtbar

3. **Edge Cases:**
   - Benutzer schließt Browser während Rollenauswahl
   - Benutzer versucht Modal zu umgehen
   - Admin ändert Rolle eines Benutzers

## 🚀 Implementierungsschritte

1. **Phase 1: Backend**
   - User Model erweitern
   - Migrations erstellen
   - API Endpoints implementieren

2. **Phase 2: Frontend**
   - RoleSelectionModal erstellen
   - AuthContext erweitern
   - Dashboard-Filterlogik

3. **Phase 3: Integration**
   - Login-Flow anpassen
   - Tests schreiben
   - Dokumentation aktualisieren

## ✅ Vorteile

- **Benutzerfreundlich:** Klare Rollenauswahl bei Erstanmeldung
- **Flexibel:** Admin kann Rollen später ändern
- **Sicher:** Rollenbasierte Zugriffskontrolle
- **Erweiterbar:** Weitere Rollen können hinzugefügt werden

---

**Status:** 📋 Konzept erstellt  
**Nächster Schritt:** Code-Analyse und Implementierung 