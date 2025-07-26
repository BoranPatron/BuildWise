# Analyse: Projekte im Frontend vs. Datenbank

## Problembeschreibung

**Behauptung**: Die Tabelle "projects" ist leer, aber im Frontend werden mehrere Projekte angezeigt.

**Tatsächliche Situation**: Die Datenbank ist NICHT leer und enthält 11 Projekte.

## Datenbank-Analyse

### Tatsächliche Datenbank-Inhalte:

```
📊 TABELLEN-ÜBERSICHT:
   📋 projects: 11 Einträge
   📋 users: 7 Einträge
   📋 audit_logs: 413 Einträge
   📋 tasks: 0 Einträge
   📋 documents: 0 Einträge
   📋 milestones: 0 Einträge
   📋 quotes: 0 Einträge
   📋 messages: 0 Einträge
   📋 cost_positions: 0 Einträge
   📋 buildwise_fees: 0 Einträge
   📋 buildwise_fee_items: 0 Einträge
   📋 sqlite_sequence: 2 Einträge
   📋 expenses: 0 Einträge

📊 PROJECTS:
   - ID 1: Toskana Luxus-Villa Boranie (Owner: 1)
   - ID 2: Tecino Lakevilla (Owner: 3)
   - ID 3: test2 (Owner: 3)
   - ID 4: test43w5 (Owner: 3)
   - ID 5: Landhaus Uster (Owner: 3)
   - ID 6: Boran Einfamilienhaus (Owner: 4)
   - ID 7: Wohnungsbau Suite (Owner: 4)
   - ID 8: Neubau Villa Berlin (Owner: 1)
   - ID 9: Neubau Villa Berlin (Owner: 1)
   - ID 10: Sanierung Hamburg (Owner: 1)
```

## API-Test-Ergebnisse

### 1. Private Projekte-API (`/api/v1/projects`)
- **Status**: 401 Unauthorized (ohne Token)
- **Status**: 401 Unauthorized (mit ungültigem Token)
- **Status**: Kein gültiger Token verfügbar

### 2. Öffentliche Projekte-API (`/api/v1/projects/public`)
- **Status**: 200 OK
- **Ergebnis**: 9 Projekte gefunden
- **Projekte**: Toskana Luxus-Villa Boranie, Tecino Lakevilla, Landhaus Uster, etc.

## Frontend-Analyse

### 1. GlobalProjects.tsx
- **API-Aufruf**: `getProjects()` → `/api/v1/projects`
- **Erwartung**: Private Projekte des angemeldeten Benutzers
- **Problem**: API gibt 401 zurück (kein gültiger Token)

### 2. Mock-Daten
- **GlobalMessages.tsx**: Verwendet Mock-Projekte für Nachrichten
- **Keine Fallback-Logik**: Frontend zeigt Fehler an, wenn API fehlschlägt

## Root Cause Analysis

### Problem 1: Authentifizierung
- **Frontend**: Versucht private Projekte zu laden (`/api/v1/projects`)
- **Backend**: Erfordert gültigen JWT-Token
- **Status**: Kein gültiger Token verfügbar → 401 Unauthorized

### Problem 2: Öffentliche Projekte
- **Backend**: `/api/v1/projects/public` gibt 9 Projekte zurück
- **Frontend**: Verwendet diese API NICHT
- **Erklärung**: Öffentliche Projekte sind für Dienstleister gedacht

### Problem 3: Token-Management
- **Frontend**: Speichert Token in localStorage
- **Problem**: Token ist möglicherweise abgelaufen oder ungültig
- **Lösung**: Benutzer muss sich neu anmelden

## Lösungsansätze

### 1. Sofortige Lösung
```bash
# Token löschen und neu anmelden
localStorage.removeItem('token');
localStorage.removeItem('user');
localStorage.removeItem('refreshToken');
```

### 2. Backend-Verbesserung
```python
# Bessere Fehlerbehandlung für 401-Fehler
@router.get("/", response_model=List[ProjectSummary])
async def read_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        projects = await get_projects_for_user(db, current_user.id)
        return projects
    except Exception as e:
        print(f"❌ Fehler beim Laden der Projekte: {e}")
        return []
```

### 3. Frontend-Verbesserung
```typescript
// Bessere Fehlerbehandlung
const loadGlobalData = async () => {
  setLoading(true);
  try {
    const projectsData = await getProjects();
    setProjects(projectsData);
    await loadGlobalStats(projectsData);
  } catch (e: any) {
    console.error('❌ Error loading global data:', e);
    if (e.message === 'Authentication required') {
      // Benutzer zur Login-Seite weiterleiten
      window.location.href = '/login';
    } else {
      setError(e.message || 'Fehler beim Laden der globalen Daten');
    }
  } finally {
    setLoading(false);
  }
};
```

## Fazit

**Die Behauptung ist falsch**: Die Datenbank ist nicht leer und enthält 11 Projekte.

**Das eigentliche Problem**: Das Frontend kann die privaten Projekte nicht laden, weil kein gültiger JWT-Token verfügbar ist.

**Lösung**: Benutzer muss sich neu anmelden, um einen gültigen Token zu erhalten.

## Empfohlene Aktionen

1. **Sofort**: Benutzer zur Login-Seite weiterleiten
2. **Kurzfristig**: Token-Validierung im Frontend verbessern
3. **Langfristig**: Automatische Token-Erneuerung implementieren 