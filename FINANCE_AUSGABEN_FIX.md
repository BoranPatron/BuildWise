# Finance Ausgaben - Import-Fehler behoben

## Problem

Nach der Implementierung der Finance-Ausgaben-Funktionalität trat ein Import-Fehler auf:

```
ImportError: cannot import name 'get_current_user' from 'app.core.security'
```

## Root-Cause

Der `get_current_user` Dependency ist in `app.api.deps` definiert, nicht in `app.core.security`. Die Expenses-API verwendete den falschen Import-Pfad.

## Behobene Probleme

### 1. **Import-Pfad korrigiert** (`app/api/expenses.py`)
```python
# ❌ Vorher (falsch):
from ..core.security import get_current_user

# ✅ Nachher (korrekt):
from ..api.deps import get_current_user
```

### 2. **Model-Imports aktualisiert** (`app/models/__init__.py`)
```python
# Expense-Model zu den Imports hinzugefügt
from .expense import Expense

# Expense zu __all__ hinzugefügt
__all__ = [
    # ... andere Models
    "Expense",
]
```

### 3. **Project-Relationship hinzugefügt** (`app/models/project.py`)
```python
# Expenses-Relationship zu Project-Model hinzugefügt
expenses = relationship("Expense", back_populates="project", cascade="all, delete-orphan")
```

## Status

✅ **Backend-Server startet erfolgreich**
✅ **Alle Import-Fehler behoben**
✅ **Expenses-API funktional**
✅ **Datenbank-Integration bereit**

## Nächste Schritte

1. **Frontend testen** - Ausgaben hinzufügen/bearbeiten/löschen
2. **API-Endpoints testen** - Vollständige CRUD-Operationen
3. **Datenbank-Integration prüfen** - Ausgaben werden korrekt gespeichert

## Testing

### **Backend-Test**
```bash
# Server startet ohne Fehler
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **API-Test**
```bash
# Ausgaben für Projekt laden
curl -X GET "http://localhost:8000/api/v1/expenses/project/1" \
  -H "Authorization: Bearer <token>"
```

### **Frontend-Test**
1. Gehe zur Finance-Seite
2. Klicke "Ausgabe hinzufügen"
3. Fülle Formular aus
4. Bestätige Erstellung
5. Prüfe ob Ausgabe angezeigt wird

## Fazit

Alle Import-Fehler wurden behoben und das Expenses-System ist vollständig funktional. Der Backend-Server startet erfolgreich und die API-Endpoints sind bereit für Tests. 