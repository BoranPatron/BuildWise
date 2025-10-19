# Spezifischer Ausschreibungs-Dokumente Filter - Implementierung

## Übersicht

Es wurde ein Filter im Dokumentenmanagementsystem (DMS) implementiert, der Dokumente nach **spezifischen Ausschreibungen** filtert. Der Filter zeigt nur diejenigen Dokumente an, die einer ausgewählten Ausschreibung zugeordnet sind über die Spalten `shared_document_ids` und `documents` in der `milestones` Tabelle.

## Implementierte Änderungen

### 1. Backend (app/api/documents.py)

**Neuer Parameter:**
- `milestone_id: Optional[int]` - Filtert nach spezifischer Ausschreibung (Milestone)

**Filter-Logik:**
```python
if milestone_id:
    # Query für spezifisches Milestone mit shared_document_ids und documents
    milestone_query = text("""
        SELECT shared_document_ids, documents 
        FROM milestones 
        WHERE id = :milestone_id 
        AND project_id = :project_id 
        AND created_by = :user_id
    """)
    
    # Verarbeite shared_document_ids
    if milestone_row.shared_document_ids:
        try:
            doc_ids = json.loads(milestone_row.shared_document_ids)
            if isinstance(doc_ids, list):
                shared_document_ids.update(str(doc_id) for doc_id in doc_ids)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Verarbeite documents (falls vorhanden)
    if milestone_row.documents:
        try:
            docs = json.loads(milestone_row.documents)
            if isinstance(docs, list):
                for doc in docs:
                    if isinstance(doc, dict) and 'id' in doc:
                        milestone_documents.add(str(doc['id']))
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Kombiniere beide Dokument-Quellen
    all_milestone_doc_ids = shared_document_ids.union(milestone_documents)
    
    # Filtere Dokumente nach den Milestone-Dokument-IDs
    if all_milestone_doc_ids:
        documents = [doc for doc in documents if str(doc.id) in all_milestone_doc_ids]
    else:
        documents = []
```

**Neuer Endpoint:**
```python
@router.get("/project/{project_id}/milestones")
async def get_project_milestones_for_filter(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt alle Milestones (Ausschreibungen) des aktuellen Benutzers für ein Projekt"""
```

### 2. Frontend API Service (Frontend/Frontend/src/api/documentService.ts)

**Erweiterte Interface:**
```typescript
export interface DocumentSearchParams {
  // ... bestehende Parameter
  milestone_id?: number;
}

export interface Milestone {
  id: number;
  title: string;
  description?: string;
  status: string;
  category?: string;
  planned_date?: string;
  created_at?: string;
}
```

**Neue Funktion:**
```typescript
export async function getProjectMilestones(project_id: number): Promise<Milestone[]> {
  try {
    const res = await api.get(`/documents/project/${project_id}/milestones`);
    return res.data;
  } catch (error) {
    console.error('Error fetching project milestones:', error);
    throw error;
  }
}
```

### 3. Frontend UI (Frontend/Frontend/src/pages/Documents.tsx)

**Neuer State:**
```typescript
const [selectedMilestone, setSelectedMilestone] = useState<number | null>(null);
const [milestones, setMilestones] = useState<Milestone[]>([]);
const [loadingMilestones, setLoadingMilestones] = useState(false);
```

**UI-Elemente:**

1. **Sidebar-Dropdown:**
```tsx
{/* Ausschreibungs-Dokumente */}
<div className="space-y-1">
  <div className="flex items-center gap-3 px-3 py-2 text-gray-300">
    <Briefcase size={18} />
    <span className="font-medium">Ausschreibungen</span>
  </div>
  <div className="ml-6">
    <select
      value={selectedMilestone || ''}
      onChange={(e) => {
        const milestoneId = e.target.value ? parseInt(e.target.value) : null;
        setSelectedMilestone(milestoneId);
        setSelectedFolder(milestoneId ? `milestone-${milestoneId}` : 'all');
      }}
      className="w-full px-3 py-2 bg-[#3d4952] border border-gray-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-[#ffbd59] focus:border-transparent"
    >
      <option value="">Alle Dokumente</option>
      {milestones.map(milestone => (
        <option key={milestone.id} value={milestone.id}>
          {milestone.title}
        </option>
      ))}
    </select>
  </div>
</div>
```

2. **Header-Dropdown:**
```tsx
{/* Ausschreibungs-Filter */}
<select
  value={selectedMilestone || ''}
  onChange={(e) => {
    const milestoneId = e.target.value ? parseInt(e.target.value) : null;
    setSelectedMilestone(milestoneId);
  }}
  className="px-4 py-2 bg-[#2c3539]/50 hover:bg-[#3d4952]/50 text-gray-400 hover:text-white border border-gray-600 rounded-lg font-medium transition-colors"
>
  <option value="">Alle Dokumente</option>
  {milestones.map(milestone => (
    <option key={milestone.id} value={milestone.id}>
      {milestone.title}
    </option>
  ))}
</select>
```

3. **Dynamischer Titel:**
```tsx
<PageHeader
  title={
    selectedMilestone 
      ? milestones.find(m => m.id === selectedMilestone)?.title || 'Ausschreibungs-Dokumente'
      : selectedCategory === 'all' 
        ? 'Alle Dokumente' 
        : (selectedCategory && DOCUMENT_CATEGORIES[selectedCategory as keyof typeof DOCUMENT_CATEGORIES]?.name) || 'Dokumente'
  }
  subtitle={`${filteredDocuments.length} von ${documents.length} Dokumente`}
/>
```

## Funktionsweise

1. **Datenbank-Schema:** Die `milestones` Tabelle hat zwei Spalten für Dokumente:
   - `shared_document_ids` (TEXT): JSON-Array mit IDs der für Ausschreibungen geteilten Dokumente
   - `documents` (JSON): Array von Dokument-Objekten mit Metadaten

2. **Filter-Logik:** 
   - Wenn eine spezifische `milestone_id` ausgewählt wird, wird das entsprechende Milestone abgefragt
   - Beide Dokument-Quellen (`shared_document_ids` und `documents`) werden verarbeitet
   - Die Dokument-IDs werden kombiniert und als Filter verwendet
   - Nur Dokumente, deren IDs in den Milestone-Dokumenten vorkommen, werden zurückgegeben

3. **UI-Integration:**
   - Dropdown-Menüs zeigen alle verfügbaren Ausschreibungen des aktuellen Projekts
   - Dynamischer Titel zeigt den Namen der ausgewählten Ausschreibung
   - Filter wird sowohl in der Sidebar als auch in der Header-Bar angeboten

## Test-Ergebnisse

Das Test-Script `test_specific_milestone_filter.py` bestätigt:
- ✅ 3 Milestones mit Dokumenten gefunden
- ✅ Milestone 2: 3 Dokumente (alle existieren)
- ✅ Milestone 1: 2 Dokumente (alle existieren)  
- ✅ Milestone 3: 0 Dokumente
- ✅ API-Simulation funktioniert korrekt
- ✅ Neue API-Endpunkte funktionieren

## Verwendung

1. **Für Bauträger:** 
   - Navigieren Sie zur DMS-Seite (`/documents`)
   - Wählen Sie ein Projekt aus
   - Verwenden Sie das Dropdown "Ausschreibungen" in der Sidebar oder Header-Bar
   - Wählen Sie eine spezifische Ausschreibung aus
   - Es werden nur Dokumente angezeigt, die dieser Ausschreibung zugeordnet sind

2. **Für Dienstleister:**
   - Der Filter ist nicht verfügbar, da Dienstleister keine Ausschreibungen erstellen

## Unterschied zur vorherigen Implementierung

**Vorher:** Filter für alle Ausschreibungs-Dokumente des Benutzers
**Jetzt:** Filter für spezifische Ausschreibung mit Dropdown-Auswahl

Die neue Implementierung ist präziser und benutzerfreundlicher, da sie eine gezielte Auswahl nach konkreten Ausschreibungen ermöglicht.

## Technische Details

- **Backend:** FastAPI mit SQLAlchemy
- **Frontend:** React mit TypeScript
- **Datenbank:** SQLite mit JSON-Spalten für Dokument-IDs
- **API:** RESTful Endpoints mit Query-Parameter `milestone_id`
- **UI:** Responsive Design mit Tailwind CSS und Dropdown-Menüs
