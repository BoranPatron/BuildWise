# Ausschreibungs-Dokumente Filter - Implementierung

## Übersicht

Es wurde ein zusätzlicher Filter im Dokumentenmanagementsystem (DMS) implementiert, der Dokumente nach den vom angemeldeten Bauträger erstellten Ausschreibungen filtert.

## Implementierte Änderungen

### 1. Backend (app/api/documents.py)

**Neuer Parameter:**
- `tender_documents_only: Optional[bool]` - Filtert nur Dokumente aus Ausschreibungen

**Filter-Logik:**
```python
if tender_documents_only:
    # Hole alle Milestones des angemeldeten Bauträgers für dieses Projekt
    milestone_query = text("""
        SELECT shared_document_ids 
        FROM milestones 
        WHERE project_id = :project_id 
        AND created_by = :user_id 
        AND shared_document_ids IS NOT NULL 
        AND shared_document_ids != ''
    """)
    
    # Sammle alle shared_document_ids
    shared_document_ids = set()
    for row in milestone_rows:
        if row.shared_document_ids:
            try:
                doc_ids = json.loads(row.shared_document_ids)
                if isinstance(doc_ids, list):
                    shared_document_ids.update(str(doc_id) for doc_id in doc_ids)
            except (json.JSONDecodeError, TypeError):
                continue
    
    # Filtere Dokumente nach shared_document_ids
    if shared_document_ids:
        documents = [doc for doc in documents if str(doc.id) in shared_document_ids]
    else:
        documents = []
```

### 2. Frontend API Service (Frontend/Frontend/src/api/documentService.ts)

**Erweiterte Interface:**
```typescript
export interface DocumentSearchParams {
  // ... bestehende Parameter
  tender_documents_only?: boolean;
}
```

### 3. Frontend UI (Frontend/Frontend/src/pages/Documents.tsx)

**Neuer State:**
```typescript
const [tenderFilter, setTenderFilter] = useState<boolean>(false);
```

**UI-Elemente:**

1. **Sidebar-Filter:**
```tsx
{/* Ausschreibungs-Dokumente */}
<div
  className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
    tenderFilter ? 'bg-[#ffbd59] text-[#1a1a2e]' : 'text-gray-300 hover:bg-[#3d4952]'
  }`}
  onClick={() => {
    setTenderFilter(!tenderFilter);
    setSelectedFolder('tender');
  }}
>
  <Briefcase size={18} />
  <span className="font-medium">Ausschreibungs-Dokumente</span>
  <span className="ml-auto text-sm">
    {tenderFilter ? 'Aktiv' : 'Alle'}
  </span>
</div>
```

2. **Header-Filter-Button:**
```tsx
{/* Ausschreibungs-Filter */}
<button
  onClick={() => setTenderFilter(!tenderFilter)}
  className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
    tenderFilter 
      ? 'bg-[#ffbd59] text-[#1a1a2e]' 
      : 'bg-[#2c3539]/50 hover:bg-[#3d4952]/50 text-gray-400 hover:text-white border border-gray-600'
  }`}
>
  <Briefcase className="w-4 h-4" />
  {tenderFilter ? 'Ausschreibungen' : 'Alle Dokumente'}
</button>
```

3. **Dynamischer Titel:**
```tsx
<PageHeader
  title={
    tenderFilter 
      ? 'Ausschreibungs-Dokumente' 
      : selectedCategory === 'all' 
        ? 'Alle Dokumente' 
        : (selectedCategory && DOCUMENT_CATEGORIES[selectedCategory as keyof typeof DOCUMENT_CATEGORIES]?.name) || 'Dokumente'
  }
  subtitle={`${filteredDocuments.length} von ${documents.length} Dokumenten`}
/>
```

## Funktionsweise

1. **Datenbank-Schema:** Die `milestones` Tabelle hat eine `shared_document_ids` Spalte (TEXT), die JSON-IDs der für Ausschreibungen geteilten Dokumente speichert.

2. **Filter-Logik:** 
   - Wenn `tender_documents_only=true` gesetzt wird, werden alle Milestones des angemeldeten Bauträgers für das aktuelle Projekt abgefragt
   - Die `shared_document_ids` werden aus den Milestones extrahiert und als JSON geparst
   - Nur Dokumente, deren IDs in den `shared_document_ids` vorkommen, werden zurückgegeben

3. **UI-Integration:**
   - Zwei Filter-Buttons: einer in der Sidebar, einer in der Header-Bar
   - Dynamischer Titel zeigt "Ausschreibungs-Dokumente" wenn Filter aktiv ist
   - Filter-Status wird visuell hervorgehoben

## Test-Ergebnisse

Das Test-Script `test_tender_filter.py` bestätigt:
- ✅ Spalte `shared_document_ids` existiert in der `milestones` Tabelle
- ✅ 2 Milestones mit geteilten Dokumenten gefunden
- ✅ 3 eindeutige geteilte Dokumente identifiziert
- ✅ 2 von 3 Dokumenten existieren in der `documents` Tabelle
- ✅ Filter-Logik funktioniert korrekt

## Verwendung

1. **Für Bauträger:** 
   - Navigieren Sie zur DMS-Seite (`/documents`)
   - Klicken Sie auf "Ausschreibungs-Dokumente" in der Sidebar oder den Filter-Button in der Header-Bar
   - Es werden nur Dokumente angezeigt, die in Ausschreibungen des angemeldeten Bauträgers verwendet werden

2. **Für Dienstleister:**
   - Der Filter ist nicht verfügbar, da Dienstleister keine Ausschreibungen erstellen

## Technische Details

- **Backend:** FastAPI mit SQLAlchemy
- **Frontend:** React mit TypeScript
- **Datenbank:** SQLite mit JSON-Spalten für `shared_document_ids`
- **API:** RESTful Endpoint mit Query-Parameter `tender_documents_only`
- **UI:** Responsive Design mit Tailwind CSS
