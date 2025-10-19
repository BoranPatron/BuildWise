# Fehlerbehebung: Documents-Spalte wird nicht berücksichtigt

## Problem
Die Filter-Logik berücksichtigte die `documents` Spalte in der `milestones` Tabelle nicht korrekt. Nur die `shared_document_ids` Spalte wurde verarbeitet.

## Ursache
1. **Falsche Datenstruktur-Annahme**: Der Code ging davon aus, dass die `documents` Spalte Dokument-Objekte mit IDs enthält
2. **Doppelt kodiertes JSON**: Die `documents` Spalte enthält doppelt kodiertes JSON (`'"[3]"'` statt `'[3]'`)

## Lösung

### 1. Korrigierte Verarbeitung der documents Spalte

**Vorher:**
```python
# Extrahiere IDs aus den Dokument-Objekten
for doc in docs:
    if isinstance(doc, dict) and 'id' in doc:
        milestone_documents.add(str(doc['id']))
```

**Nachher:**
```python
# Handle doppelt kodiertes JSON (falls vorhanden)
docs_raw = milestone_row.documents
if isinstance(docs_raw, str) and docs_raw.startswith('"') and docs_raw.endswith('"'):
    # Entferne äußere Anführungszeichen
    docs_raw = docs_raw[1:-1]

docs = json.loads(docs_raw)
if isinstance(docs, list):
    # Die documents Spalte enthält direkt die Dokument-IDs als Array
    milestone_documents.update(str(doc_id) for doc_id in docs)
```

### 2. Datenbank-Struktur-Analyse

**Milestone 1 (Maler- und Innenausbauarbeiten):**
- `shared_document_ids`: `'[2, 1]'` → Dokumente 1, 2
- `documents`: `'null'` → Keine zusätzlichen Dokumente

**Milestone 3 (Sanitär- und Heizungsinstallation):**
- `shared_document_ids`: `None` → Keine geteilten Dokumente
- `documents`: `'"[3]"'` → Dokument 3 (doppelt kodiert)

## Test-Ergebnisse

**Vorher:**
- Milestone 1: 2 Dokumente (nur shared_document_ids)
- Milestone 3: 0 Dokumente (documents nicht verarbeitet)

**Nachher:**
- Milestone 1: 2 Dokumente (shared_document_ids: 1, 2)
- Milestone 3: 1 Dokument (documents: 3)

## API-Test

```
Milestone 1:
  Status: 200
  Dokumente: 2
    - 2: BuildWise_Beispielprojekt_Project_Charter
    - 1: Baugenehmigung_Turm_der_tausend_Sterne

Milestone 3:
  Status: 200
  Dokumente: 1
    - 3: buildwise_invoice_1
```

## Ergebnis

✅ Beide Spalten (`shared_document_ids` und `documents`) werden korrekt verarbeitet
✅ Doppelt kodiertes JSON wird korrekt dekodiert
✅ Filter-Logik funktioniert für alle Dokument-Quellen
✅ API gibt korrekte Ergebnisse zurück
✅ Keine Linter-Fehler

Der spezifische Ausschreibungs-Dokumente Filter berücksichtigt jetzt vollständig beide Dokument-Quellen in der `milestones` Tabelle!
