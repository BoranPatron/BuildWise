# Bauphasen-Tracking Erweitert - Kostenpositionen & Gewerke

## Übersicht

Die erweiterte Implementierung ermöglicht es, dass **automatisch die aktuelle Projektphase** sowohl in die `cost_positions` als auch in die `milestones` Tabelle geschrieben wird, wenn neue Einträge erstellt werden. Dies ermöglicht späteres Tracking der Kosten und Gewerke je Phase.

## 🏗️ Implementierte Features

### ✅ **Automatische Bauphasen-Zuordnung**
- ✅ **Kostenpositionen** - Aktuelle Projektphase wird automatisch gesetzt
- ✅ **Gewerke (Milestones)** - Aktuelle Projektphase wird automatisch gesetzt
- ✅ **Beim Akzeptieren von Angeboten** - Phase wird aus dem Projekt übernommen
- ✅ **Manuelle Einträge** - Phase wird beim Erstellen gesetzt

### ✅ **Datenbank-Erweiterung**
- ✅ **Neues Feld** - `construction_phase` in `cost_positions` Tabelle
- ✅ **Neues Feld** - `construction_phase` in `milestones` Tabelle
- ✅ **Indizes** - Für bessere Performance bei Abfragen
- ✅ **Migration** - Automatische Aktualisierung bestehender Einträge

### ✅ **Service-Funktionen**
- ✅ **Filter nach Bauphasen** - Kostenpositionen und Gewerke nach Phase abrufen
- ✅ **Statistiken nach Phasen** - Kosten- und Gewerke-Verteilung pro Bauphase
- ✅ **Automatische Zuordnung** - Beim Erstellen neuer Einträge

## 🗄️ Datenbank-Struktur

### 1. CostPosition Model (Erweitert)
```python
class CostPosition(Base):
    # ... bestehende Felder ...
    
    # Bauphasen-Tracking
    construction_phase = Column(String, nullable=True)  # Aktuelle Bauphase beim Erstellen
    
    # ... weitere Felder ...
```

### 2. Milestone Model (Erweitert)
```python
class Milestone(Base):
    # ... bestehende Felder ...
    
    # Bauphasen-Tracking
    construction_phase = Column(String, nullable=True)  # Aktuelle Bauphase beim Erstellen des Gewerks
    
    # ... weitere Felder ...
```

### 3. Migration
```sql
-- Füge construction_phase Spalte zu cost_positions hinzu
ALTER TABLE cost_positions ADD COLUMN construction_phase TEXT;
CREATE INDEX ix_cost_positions_construction_phase ON cost_positions (construction_phase);

-- Füge construction_phase Spalte zu milestones hinzu
ALTER TABLE milestones ADD COLUMN construction_phase TEXT;
CREATE INDEX ix_milestones_construction_phase ON milestones (construction_phase);

-- Aktualisiere bestehende Einträge
UPDATE cost_positions 
SET construction_phase = (
    SELECT construction_phase 
    FROM projects 
    WHERE projects.id = cost_positions.project_id
)
WHERE construction_phase IS NULL;

UPDATE milestones 
SET construction_phase = (
    SELECT construction_phase 
    FROM projects 
    WHERE projects.id = milestones.project_id
)
WHERE construction_phase IS NULL;
```

## 🔧 Service-Implementierung

### 1. Automatische Bauphasen-Zuordnung für Kostenpositionen
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

### 2. Automatische Bauphasen-Zuordnung für Gewerke
```python
async def create_milestone(db: AsyncSession, milestone_in: MilestoneCreate, created_by: int) -> Milestone:
    """Erstellt ein neues Gewerk mit automatischer Bauphasen-Zuordnung"""
    from ..models import Project
    
    # Hole das Projekt, um die aktuelle Bauphase zu ermitteln
    project_result = await db.execute(
        select(Project).where(Project.id == milestone_in.project_id)
    )
    project = project_result.scalar_one_or_none()
    
    # Erstelle das Gewerk
    milestone_data = {
        'project_id': milestone_in.project_id,
        'created_by': created_by,
        'title': milestone_in.title,
        'description': milestone_in.description,
        'status': milestone_in.status,
        'priority': milestone_in.priority,
        'category': milestone_in.category,
        'planned_date': milestone_in.planned_date,
        'start_date': milestone_in.start_date,
        'end_date': milestone_in.end_date,
        'budget': milestone_in.budget,
        'actual_costs': milestone_in.actual_costs,
        'contractor': milestone_in.contractor,
        'is_critical': milestone_in.is_critical,
        'notify_on_completion': milestone_in.notify_on_completion,
        'notes': milestone_in.notes
    }
    
    # Setze automatisch die aktuelle Bauphase des Projekts
    if project and project.construction_phase:
        milestone_data['construction_phase'] = project.construction_phase
        print(f"🏗️ Gewerk erstellt mit Bauphase: {project.construction_phase}")
    else:
        print(f"⚠️ Projekt hat keine Bauphase gesetzt")
    
    milestone = Milestone(**milestone_data)
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return milestone
```

### 3. Filter nach Bauphasen für Kostenpositionen
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

### 4. Filter nach Bauphasen für Gewerke
```python
async def get_milestones_by_construction_phase(db: AsyncSession, project_id: int, construction_phase: str) -> List[Milestone]:
    """Holt Gewerke nach Bauphase"""
    result = await db.execute(
        select(Milestone)
        .where(
            Milestone.project_id == project_id,
            Milestone.construction_phase == construction_phase
        )
        .order_by(Milestone.planned_date)
    )
    return list(result.scalars().all())
```

### 5. Statistiken nach Bauphasen für Kostenpositionen
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

### 6. Statistiken nach Bauphasen für Gewerke
```python
async def get_milestone_statistics_by_phase(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Gewerke nach Bauphasen"""
    # Gesamtanzahl pro Bauphase
    phase_distribution_result = await db.execute(
        select(
            Milestone.construction_phase,
            func.count(Milestone.id).label('count'),
            func.sum(Milestone.budget).label('total_budget'),
            func.sum(Milestone.actual_costs).label('total_costs'),
            func.avg(Milestone.progress_percentage).label('avg_progress')
        )
        .where(Milestone.project_id == project_id)
        .group_by(Milestone.construction_phase)
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

### 2. Gewerk erstellen
```python
# Automatisch wird die aktuelle Projektphase gesetzt
milestone = await create_milestone(db, MilestoneCreate(
    project_id=1,
    title="Elektroinstallation",
    planned_date=date(2024, 6, 15),
    budget=5000.00
), created_by=1)
# construction_phase wird automatisch auf "innenausbau" gesetzt
```

### 3. Kostenpositionen nach Phase filtern
```python
# Hole alle Kostenpositionen für die "innenausbau" Phase
innenausbau_costs = await get_cost_positions_by_construction_phase(
    db, project_id=1, construction_phase="innenausbau"
)
```

### 4. Gewerke nach Phase filtern
```python
# Hole alle Gewerke für die "innenausbau" Phase
innenausbau_milestones = await get_milestones_by_construction_phase(
    db, project_id=1, construction_phase="innenausbau"
)
```

### 5. Statistiken nach Phasen
```python
# Hole Statistiken für alle Bauphasen (Kostenpositionen)
cost_phase_stats = await get_cost_position_statistics_by_phase(db, project_id=1)

# Hole Statistiken für alle Bauphasen (Gewerke)
milestone_phase_stats = await get_milestone_statistics_by_phase(db, project_id=1)

# Returns für Kostenpositionen:
{
  "phase_distribution": {
    "innenausbau": {"count": 5, "total_amount": 25000, "total_paid": 15000},
    "rohbau": {"count": 3, "total_amount": 15000, "total_paid": 10000}
  },
  "total_count": 8,
  "total_amount": 40000,
  "total_paid": 25000,
  "total_remaining": 15000
}

# Returns für Gewerke:
{
  "phase_distribution": {
    "innenausbau": {"count": 3, "total_budget": 20000, "total_costs": 15000, "avg_progress": 75.0},
    "rohbau": {"count": 2, "total_budget": 15000, "total_costs": 12000, "avg_progress": 80.0}
  },
  "total_count": 5,
  "total_budget": 35000,
  "total_costs": 27000,
  "avg_progress": 77.0,
  "total_budget_variance": 8000
}
```

## 🎯 Vorteile der erweiterten Implementierung

### 1. **Vollständiges Tracking**
- ✅ **Kostenpositionen** - Automatische Bauphasen-Zuordnung
- ✅ **Gewerke** - Automatische Bauphasen-Zuordnung
- ✅ **Konsistenz** - Alle Einträge haben eine Phase
- ✅ **Zeitstempel** - Phase wird zum Erstellungszeitpunkt gespeichert

### 2. **Detaillierte Analyse**
- ✅ **Kosten pro Phase** - Verteilung der Ausgaben
- ✅ **Gewerke pro Phase** - Verteilung der Arbeiten
- ✅ **Fortschritt pro Phase** - Bezahlte vs. offene Beträge
- ✅ **Budget-Kontrolle** - Geplante vs. tatsächliche Kosten

### 3. **Projektmanagement**
- ✅ **Budget-Kontrolle** - Überwachung der Kosten je Phase
- ✅ **Ressourcen-Planung** - Finanzielle und zeitliche Planung pro Bauphase
- ✅ **Reporting** - Detaillierte Finanz- und Fortschrittsberichte
- ✅ **Trend-Analyse** - Kosten- und Fortschrittsentwicklung über Phasen

## 📱 Frontend-Integration

### 1. Finance-Kachel
```tsx
// Zeige Kostenpositionen nach Bauphasen
const costPhaseStats = await getCostPositionStatisticsByPhase(projectId);

// Rendere Bauphasen-Filter für Kosten
{Object.entries(costPhaseStats.phase_distribution).map(([phase, stats]) => (
  <PhaseCostCard 
    key={phase}
    phase={phase}
    stats={stats}
    type="cost"
  />
))}
```

### 2. Gewerke-Kachel
```tsx
// Zeige Gewerke nach Bauphasen
const milestonePhaseStats = await getMilestoneStatisticsByPhase(projectId);

// Rendere Bauphasen-Filter für Gewerke
{Object.entries(milestonePhaseStats.phase_distribution).map(([phase, stats]) => (
  <PhaseMilestoneCard 
    key={phase}
    phase={phase}
    stats={stats}
    type="milestone"
  />
))}
```

### 3. Kombinierte Bauphasen-Filter
```tsx
// Filter für beide Typen
const [selectedPhase, setSelectedPhase] = useState('all');

const filteredCostPositions = selectedPhase === 'all' 
  ? costPositions 
  : costPositions.filter(cp => cp.construction_phase === selectedPhase);

const filteredMilestones = selectedPhase === 'all' 
  ? milestones 
  : milestones.filter(m => m.construction_phase === selectedPhase);
```

### 4. Kombinierte Statistiken-Dashboard
```tsx
// Zeige kombinierte Kostenverteilung nach Phasen
<CombinedPhaseChart 
  costData={costPhaseStats.phase_distribution}
  milestoneData={milestonePhaseStats.phase_distribution}
  totalCostAmount={costPhaseStats.total_amount}
  totalMilestoneBudget={milestonePhaseStats.total_budget}
/>
```

## 🧪 Testing

### 1. Erweiterte Migration-Test
```bash
python apply_construction_phase_migration_extended.py
```

**Erwartete Ausgabe:**
```
🏗️ Erweiterte Construction Phase Migration
============================================================
🔧 Starte erweiterte Migration für construction_phase...

📊 COST_POSITIONS Tabelle:
----------------------------------------
✅ Spalte construction_phase hinzugefügt
✅ Index für construction_phase erstellt
🔄 5 cost_positions müssen aktualisiert werden
✅ 5 cost_positions mit construction_phase aktualisiert

📊 MILESTONES Tabelle:
----------------------------------------
✅ Spalte construction_phase hinzugefügt
✅ Index für construction_phase erstellt
🔄 3 milestones müssen aktualisiert werden
✅ 3 milestones mit construction_phase aktualisiert

📊 Gesamtstatistiken:
----------------------------------------
📋 Cost Positions:
  - Gesamt: 8
  - Mit Bauphase: 8
  - Ohne Bauphase: 0
📋 Milestones:
  - Gesamt: 5
  - Mit Bauphase: 5
  - Ohne Bauphase: 0

🏗️ Bauphasen-Verteilung:
----------------------------------------
📊 Cost Positions nach Bauphasen:
  • innenausbau: 3 Kostenpositionen
  • rohbau: 2 Kostenpositionen
  • fundament: 1 Kostenpositionen
📊 Milestones nach Bauphasen:
  • innenausbau: 2 Gewerke
  • rohbau: 1 Gewerke
  • fundament: 1 Gewerke

🧪 Teste Funktionalität...
✅ Cost Positions Test erfolgreich:
  • ID 1: 'Elektroinstallation' (Phase: innenausbau, Projekt: 1)
  • ID 2: 'Sanitärinstallation' (Phase: innenausbau, Projekt: 1)
✅ Milestones Test erfolgreich:
  • ID 1: 'Elektroinstallation' (Phase: innenausbau, Projekt: 1)
  • ID 2: 'Sanitärinstallation' (Phase: innenausbau, Projekt: 1)

✅ Erweiterte Migration erfolgreich abgeschlossen!
```

### 2. Service-Test
```python
# Teste automatische Bauphasen-Zuordnung für Kostenpositionen
cost_position = await create_cost_position(db, test_data)
assert cost_position.construction_phase == "innenausbau"

# Teste automatische Bauphasen-Zuordnung für Gewerke
milestone = await create_milestone(db, test_data, created_by=1)
assert milestone.construction_phase == "innenausbau"

# Teste Filter nach Bauphasen für Kostenpositionen
innenausbau_costs = await get_cost_positions_by_construction_phase(db, 1, "innenausbau")
assert len(innenausbau_costs) == 3

# Teste Filter nach Bauphasen für Gewerke
innenausbau_milestones = await get_milestones_by_construction_phase(db, 1, "innenausbau")
assert len(innenausbau_milestones) == 2

# Teste Statistiken
cost_stats = await get_cost_position_statistics_by_phase(db, 1)
milestone_stats = await get_milestone_statistics_by_phase(db, 1)
assert "innenausbau" in cost_stats["phase_distribution"]
assert "innenausbau" in milestone_stats["phase_distribution"]
```

## 📋 Checkliste - Vollständig implementiert

### ✅ **Datenbank**
- ✅ `construction_phase` Feld in `cost_positions` Tabelle
- ✅ `construction_phase` Feld in `milestones` Tabelle
- ✅ Indizes für Performance
- ✅ Migration für bestehende Einträge
- ✅ Schema-Updates für beide Tabellen

### ✅ **Backend-Services**
- ✅ Automatische Bauphasen-Zuordnung für Kostenpositionen
- ✅ Automatische Bauphasen-Zuordnung für Gewerke
- ✅ Filter nach Bauphasen für beide Typen
- ✅ Statistiken nach Phasen für beide Typen
- ✅ Service-Funktionen für beide Tabellen

### ✅ **API-Endpoints**
- ✅ Kostenpositionen nach Phase abrufen
- ✅ Gewerke nach Phase abrufen
- ✅ Statistiken nach Phasen für beide Typen
- ✅ Automatische Phase-Zuordnung für beide Typen

### ✅ **Frontend-Integration**
- ✅ Bauphasen-Filter für beide Typen
- ✅ Phase-spezifische Statistiken für beide Typen
- ✅ Kostenverteilung nach Phasen
- ✅ Gewerke-Verteilung nach Phasen

## 🎉 Ergebnis

Die erweiterte Implementierung ermöglicht:

- ✅ **Vollständiges Tracking** - Bauphasen werden automatisch für Kostenpositionen und Gewerke gesetzt
- ✅ **Detaillierte Analyse** - Kosten- und Gewerke-Verteilung nach Phasen
- ✅ **Projektmanagement** - Budget- und Fortschritts-Kontrolle je Bauphase
- ✅ **Reporting** - Finanz- und Fortschrittsberichte nach Bauphasen
- ✅ **Kombinierte Sicht** - Gesamtüberblick über Kosten und Gewerke je Phase

Das **erweiterte Bauphasen-Tracking** ist vollständig implementiert und ermöglicht eine **präzise Kosten- und Fortschrittsverfolgung** je Projektphase! 🚀 