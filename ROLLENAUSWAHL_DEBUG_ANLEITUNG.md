# Rollenauswahl Debug-Funktionalität

## Übersicht
Für das Testen der Rollenauswahl-Modal wurde eine Debug-Funktionalität implementiert, die nur im Entwicklungsmodus verfügbar ist.

## Neue Modal-Flag Logik

### `role_selection_modal_shown` Flag
- **Zweck**: Verhindert mehrfache Anzeige des Modals
- **Funktionsweise**: 
  - Wird auf `true` gesetzt wenn Modal angezeigt wird
  - Modal erscheint nicht mehr, auch wenn User technisch noch "neu" ist
  - Nur der Debug-Button kann das Flag zurücksetzen

### Logik-Reihenfolge:
1. **Modal bereits angezeigt?** → Kein Modal (auch bei neuen Usern)
2. **User neu (< 24h) UND keine Rolle?** → Modal anzeigen
3. **Alter User ohne Rolle?** → Modal anzeigen (Edge-Case)
4. **Sonst** → Kein Modal

## Debug-Buttons auf dem Dashboard

### 🔍 User Status (Debug)
- **Zweck**: Zeigt den aktuellen User-Status in der Browser-Konsole an
- **Informationen**: 
  - Komplette User-Daten
  - Rollen-Status (`hasRole`, `roleSelected`)
  - **Modal-Status (`role_selection_modal_shown`)**
  - Erstellungsdatum (`createdAt`)
  - Subscription-Plan
- **Verwendung**: Klicken → Konsole öffnen (F12) → User-Status prüfen

### 🔧 Reset Rolle (Debug)
- **Zweck**: Setzt die User-Rolle zurück und markiert den User als "neu"
- **Funktionen**:
  - Entfernt `user_role` und setzt `role_selected = false`
  - **Setzt `role_selection_modal_shown = false`** (ermöglicht Modal erneut)
  - Setzt `created_at` auf aktuelles Datum (macht User "neu")
  - Resettet Onboarding-Status
  - Lädt Seite neu um Modal zu triggern

## Backend-Endpoints

### POST `/api/v1/auth/select-role`
```json
{
  "message": "Rolle erfolgreich ausgewählt",
  "role": "bautraeger",
  "role_selected": true
}
```
**Neues Verhalten**: Setzt automatisch `role_selection_modal_shown = true`

### POST `/api/v1/auth/mark-modal-shown`
```json
{
  "message": "Modal-Flag erfolgreich gesetzt",
  "user_id": 3
}
```
**Zweck**: Markiert dass Modal angezeigt wurde (optional, wird auch automatisch bei Rollenauswahl gesetzt)

### POST `/api/v1/auth/debug/reset-role`
```json
{
  "message": "Rolle erfolgreich zurückgesetzt (DEBUG)",
  "user_id": 3,
  "reset_timestamp": "2025-01-22T18:51:39.496075+00:00"
}
```
**Neues Verhalten**: Setzt auch `role_selection_modal_shown = false` zurück

## Verwendung für Tests

### 1. Modal-Test durchführen:
1. Auf Dashboard gehen
2. "🔧 Reset Rolle (Debug)" Button klicken
3. Bestätigung abwarten
4. Seite lädt neu → Rollenauswahl-Modal erscheint
5. Rolle auswählen → **Modal wird nie wieder angezeigt**
6. Für erneuten Test: Debug-Button erneut verwenden

### 2. User-Status prüfen:
```javascript
// Konsolen-Output nach "🔍 User Status (Debug)" Klick
{
  user: {...},
  hasRole: false,
  roleSelected: false,
  role_selection_modal_shown: false,  // ← Neues Flag
  createdAt: "2025-01-22T18:51:39.496075+00:00",
  subscriptionPlan: "basis"
}
```

### 3. Modal-Verhalten testen:
- **Szenario 1**: Neuer User ohne Modal-Flag → Modal erscheint
- **Szenario 2**: Neuer User mit Modal-Flag → Modal erscheint NICHT
- **Szenario 3**: Nach Rollenauswahl → Modal erscheint nie wieder
- **Szenario 4**: Nach Debug-Reset → Modal erscheint wieder

## Technische Details

### Frontend-Logik (OnboardingManager):
```typescript
static getOnboardingState(user: User): OnboardingState {
  // 1. Erste Priorität: Modal bereits angezeigt?
  if (user.role_selection_modal_shown) {
    return {
      needsOnboarding: false,
      reason: "Rollenauswahl-Modal bereits angezeigt"
    };
  }

  // 2. Neue User ohne Rolle
  const isNewUser = this.isNewUser(user);
  if (isNewUser && (!user.role_selected || !user.user_role)) {
    return {
      needsOnboarding: true,
      reason: "Neuer User - Rollenauswahl erforderlich"
    };
  }
  
  // ... weitere Logik
}
```

### Backend-Logik (auth.py):
```python
# Bei Rollenauswahl
await db.execute(
    update(User)
    .where(User.id == current_user.id)
    .values(
        user_role=role_enum,
        role_selected=True,
        role_selected_at=datetime.utcnow(),
        role_selection_modal_shown=True  # ← Neues Flag
    )
)

# Bei Debug-Reset
await db.execute(
    update(User)
    .where(User.id == current_user.id)
    .values(
        user_role=None,
        role_selected=False,
        role_selection_modal_shown=False,  # ← Flag zurücksetzen
        created_at=datetime.now(timezone.utc)
    )
)
```

### Datenbank-Schema:
```sql
ALTER TABLE users ADD COLUMN role_selection_modal_shown BOOLEAN DEFAULT FALSE;
```

## Vorteile der neuen Logik

### ✅ **Verbesserte Benutzererfahrung:**
- Modal erscheint nur einmal pro User
- Kein nerviges Wiederholen bei Seitenreloads
- Klare Trennung zwischen "angezeigt" und "ausgewählt"

### ✅ **Robuste Test-Funktionalität:**
- Debug-Button kann Modal-Anzeige zurücksetzen
- Vollständige Kontrolle über Modal-Verhalten
- Wiederholbare Tests möglich

### ✅ **Sichere Implementierung:**
- Flag wird automatisch bei Rollenauswahl gesetzt
- Verhindert Umgehung durch Browser-Refresh
- Datenbankgesteuerte Logik

## Troubleshooting

### Modal erscheint trotz Flag:
1. User-Status prüfen: `role_selection_modal_shown` sollte `true` sein
2. OnboardingManager-Logs in Konsole prüfen
3. Backend-Logs auf Fehler prüfen

### Modal erscheint nicht trotz Reset:
1. Debug-Button erfolgreich? → Konsole prüfen
2. `role_selection_modal_shown` sollte `false` sein
3. `created_at` sollte aktuell sein (< 24h)
4. Browser-Cache leeren und neu laden

### Flag wird nicht gesetzt:
1. Backend-Endpoint erreichbar? → Netzwerk-Tab prüfen
2. JWT-Token gültig? → 401-Fehler in Konsole?
3. Datenbank-Spalte existiert? → Backend-Logs prüfen 