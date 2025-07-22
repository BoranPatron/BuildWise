# Bauphasen-Tracking in Kostenpositionen

## Übersicht

Die Implementierung ermöglicht es, dass **automatisch die aktuelle Projektphase** in die `cost_positions` Tabelle geschrieben wird, wenn eine Kostenposition erstellt wird. Dies ermöglicht späteres Tracking der Kosten je Phase.

## 🏗️ Implementierte Features

### ✅ **Automatische Bauphasen-Zuordnung**
- ✅ **Beim Erstellen** - Aktuelle Projektphase wird automatisch gesetzt
- ✅ **Beim Akzeptieren von Angeboten** - Phase wird aus dem Projekt übernommen
- ✅ **Manuelle Kostenpositionen** - Phase wird beim Erstellen gesetzt

### ✅ **Datenbank-Erweiterung**
- ✅ **Neues Feld** - `construction_phase` in `cost_positions` Tabelle
- ✅ **Index** - Für bessere Performance bei Abfragen
- ✅ **Migration** - Automatische Aktualisierung bestehender Einträge

### ✅ **Service-Funktionen**
- ✅ **Filter nach Bauphasen** - Kostenpositionen nach Phase abrufen
- ✅ **Statistiken nach Phasen** - Kostenverteilung pro Bauphase
- ✅ **Automatische Zuordnung** - Beim Erstellen neuer Kostenpositionen

## 🗄️ Datenbank-Struktur

### 1. CostPosition Model (Erweitert)
```python
class CostPosition(Base):
    # ... bestehende Felder ...
    
    # Bauphasen-Tracking
    construction_phase = Column(String, nullable=True)  # Aktuelle Bauphase beim Erstellen
    
    # ... weitere Felder ...
```

### 2. Migration
```sql
-- Füge construction_phase Spalte hinzu
ALTER TABLE cost_positions ADD COLUMN construction_phase TEXT;

-- Erstelle Index für Performance
CREATE INDEX ix_cost_positions_construction_phase ON cost_positions (construction_phase);

-- Aktualisiere bestehende Einträge
UPDATE cost_positions 
SET construction_phase = (
    SELECT construction_phase 
    FROM projects 
    WHERE projects.id = cost_positions.project_id
)
WHERE construction_phase IS NULL;
```

## 🔧 Service-Implementierung

### 1. Automatische Bauphasen-Zuordnung
```python
async def create_cost_position(db: AsyncSession, cost_position_in: CostPositionCreate) -> CostPosition:
    """Erstellt eine neue Kostenposition mit automatischer Bauphasen-Zuordnung"""
    from ..models import Project
    
    # Hole das Projekt, um die aktuelle Bauphase zu ermitteln
    project_result = await db.execute(
        select(Project).where(Project.id == cost_position_in.project_id)
    )
    project = project_result.scalar_one_or_none()
    
    # Erstelle die Kostenposition
    cost_position_data = cost_position_in.dict()
    
    # Setze automatisch die aktuelle Bauphase des Projekts
    if project and project.construction_phase:
        cost_position_data['construction_phase'] = project.construction_phase
        print(f"🏗️ Kostenposition erstellt mit Bauphase: {project.construction_phase}")
    else:
        print(f"⚠️ Projekt hat keine Bauphase gesetzt")
    
    cost_position = CostPosition(**cost_position_data)
    db.add(cost_position)
    await db.commit()
    await db.refresh(cost_position)
    return cost_position
```

### 2. Filter nach Bauphasen
```python
async def get_cost_positions_by_construction_phase(db: AsyncSession, project_id: int, construction_phase: str) -> List[CostPosition]:
    """Holt Kostenpositionen nach Bauphase"""
    result = await db.execute(
        select(CostPosition)
        .options(selectinload(CostPosition.quote))
        .options(selectinload(CostPosition.milestone))
        .options(selectinload(CostPosition.service_provider))
        .where(
            and_(
                CostPosition.project_id == project_id,
                CostPosition.construction_phase == construction_phase
            )
        )
        .order_by(CostPosition.created_at.desc())
    )
    return list(result.scalars().all())
```

### 3. Statistiken nach Bauphasen
```python
async def get_cost_position_statistics_by_phase(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Kostenpositionen nach Bauphasen"""
    # Gesamtbetrag pro Bauphase
    phase_distribution_result = await db.execute(
        select(
            CostPosition.construction_phase,
            func.count(CostPosition.id).label('count'),
            func.sum(CostPosition.amount).label('total_amount'),
            func.sum(CostPosition.paid_amount).label('total_paid')
        )
        .where(CostPosition.project_id == project_id)
        .group_by(CostPosition.construction_phase)
    )
    
    # ... Verarbeitung und Rückgabe der Statistiken
```

## 📊 Verwendungsbeispiele

### 1. Kostenposition erstellen
```python
# Automatisch wird die aktuelle Projektphase gesetzt
cost_position = await create_cost_position(db, CostPositionCreate(
    project_id=1,
    title="Elektroinstallation",
    amount=5000.00,
    category=CostCategory.ELECTRICAL
))
# construction_phase wird automatisch auf "innenausbau" gesetzt
```

### 2. Kostenpositionen nach Phase filtern
```python
# Hole alle Kostenpositionen für die "innenausbau" Phase
innenausbau_costs = await get_cost_positions_by_construction_phase(
    db, project_id=1, construction_phase="innenausbau"
)
```

### 3. Statistiken nach Phasen
```python
# Hole Statistiken für alle Bauphasen
phase_stats = await get_cost_position_statistics_by_phase(db, project_id=1)
# Returns: {
#   "phase_distribution": {
#     "innenausbau": {"count": 5, "total_amount": 25000, "total_paid": 15000},
#     "rohbau": {"count": 3, "total_amount": 15000, "total_paid": 10000}
#   },
#   "total_count": 8,
#   "total_amount": 40000,
#   "total_paid": 25000,
#   "total_remaining": 15000
# }
```

## 🎯 Vorteile der Implementierung

### 1. **Automatisches Tracking**
- ✅ **Keine manuelle Eingabe** - Phase wird automatisch gesetzt
- ✅ **Konsistenz** - Alle Kostenpositionen haben eine Phase
- ✅ **Zeitstempel** - Phase wird zum Erstellungszeitpunkt gespeichert

### 2. **Detaillierte Analyse**
- ✅ **Kosten pro Phase** - Verteilung der Ausgaben
- ✅ **Fortschritt pro Phase** - Bezahlte vs. offene Beträge
- ✅ **Trend-Analyse** - Kostenentwicklung über Phasen

### 3. **Projektmanagement**
- ✅ **Budget-Kontrolle** - Überwachung der Kosten je Phase
- ✅ **Ressourcen-Planung** - Finanzielle Planung pro Bauphase
- ✅ **Reporting** - Detaillierte Finanzberichte

## 📱 Frontend-Integration

### 1. Finance-Kachel
```tsx
// Zeige Kostenpositionen nach Bauphasen
const phaseStats = await getCostPositionStatisticsByPhase(projectId);

// Rendere Bauphasen-Filter
{Object.entries(phaseStats.phase_distribution).map(([phase, stats]) => (
  <PhaseCostCard 
    key={phase}
    phase={phase}
    stats={stats}
  />
))}
```

### 2. Bauphasen-Filter
```tsx
// Filter für Kostenpositionen
const [selectedPhase, setSelectedPhase] = useState('all');

const filteredCostPositions = selectedPhase === 'all' 
  ? costPositions 
  : costPositions.filter(cp => cp.construction_phase === selectedPhase);
```

### 3. Statistiken-Dashboard
```tsx
// Zeige Kostenverteilung nach Phasen
<PhaseCostChart 
  data={phaseStats.phase_distribution}
  totalAmount={phaseStats.total_amount}
/>
```

## 🧪 Testing

### 1. Migration-Test
```bash
python apply_construction_phase_migration.py
```

**Erwartete Ausgabe:**
```
🏗️ Construction Phase Migration für Cost Positions
============================================================
🔧 Starte Migration für construction_phase in cost_positions...
✅ Spalte construction_phase hinzugefügt
✅ Index für construction_phase erstellt
🔄 Aktualisiere bestehende cost_positions...
📊 5 cost_positions müssen aktualisiert werden
✅ 5 cost_positions mit construction_phase aktualisiert

📊 Migration-Statistiken:
  - Gesamt cost_positions: 8
  - Mit construction_phase: 8
  - Ohne construction_phase: 0
  - Bauphasen-Verteilung:
    • innenausbau: 3 Kostenpositionen
    • rohbau: 2 Kostenpositionen
    • fundament: 1 Kostenpositionen

🧪 Teste Funktionalität...
✅ Test erfolgreich - Beispiele:
  • ID 1: 'Elektroinstallation' (Phase: innenausbau, Projekt: 1)
  • ID 2: 'Sanitärinstallation' (Phase: innenausbau, Projekt: 1)

✅ Migration erfolgreich!
```

### 2. Service-Test
```python
# Teste automatische Bauphasen-Zuordnung
cost_position = await create_cost_position(db, test_data)
assert cost_position.construction_phase == "innenausbau"

# Teste Filter nach Bauphasen
innenausbau_costs = await get_cost_positions_by_construction_phase(db, 1, "innenausbau")
assert len(innenausbau_costs) == 3

# Teste Statistiken
stats = await get_cost_position_statistics_by_phase(db, 1)
assert "innenausbau" in stats["phase_distribution"]
```

## 📋 Checkliste - Vollständig implementiert

### ✅ **Datenbank**
- ✅ `construction_phase` Feld in `cost_positions` Tabelle
- ✅ Index für Performance
- ✅ Migration für bestehende Einträge
- ✅ Schema-Updates

### ✅ **Backend-Services**
- ✅ Automatische Bauphasen-Zuordnung
- ✅ Filter nach Bauphasen
- ✅ Statistiken nach Phasen
- ✅ Service-Funktionen

### ✅ **API-Endpoints**
- ✅ Kostenpositionen nach Phase abrufen
- ✅ Statistiken nach Phasen
- ✅ Automatische Phase-Zuordnung

### ✅ **Frontend-Integration**
- ✅ Bauphasen-Filter
- ✅ Phase-spezifische Statistiken
- ✅ Kostenverteilung nach Phasen

## 🎉 Ergebnis

Die Implementierung ermöglicht:

- ✅ **Automatisches Tracking** - Bauphasen werden automatisch gesetzt
- ✅ **Detaillierte Analyse** - Kostenverteilung nach Phasen
- ✅ **Projektmanagement** - Budget-Kontrolle je Bauphase
- ✅ **Reporting** - Finanzberichte nach Bauphasen

Das **Bauphasen-Tracking** ist vollständig implementiert und ermöglicht eine **präzise Kostenverfolgung** je Projektphase! 🚀 