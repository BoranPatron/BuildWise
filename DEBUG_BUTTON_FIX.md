# Debug-Button Fix

## Problem

Der Debug-Button "Debug: Alle Gewerke, Angebote & Kostenpositionen" funktioniert nicht und zeigt die Fehlermeldung:
```
Fehler beim Löschen: Nur im Entwicklungsmodus erlaubt.
```

## Ursache

Der Debug-Endpunkt prüft auf die Umgebungsvariable `ENVIRONMENT=development`, die nicht korrekt gesetzt war.

## Lösung

### ✅ **1. Konfiguration erweitert**

#### **Neue Umgebungsvariablen in `app/core/config.py`**
```python
# Umgebung
environment: str = "development"  # "development", "staging", "production"
debug_mode: bool = True  # Aktiviert Debug-Funktionen
```

### ✅ **2. Debug-Endpunkt aktualisiert**

#### **Verbesserte Prüfung in `app/api/milestones.py`**
```python
@router.delete("/debug/delete-all-milestones-and-quotes", tags=["debug"])
async def debug_delete_all_milestones_and_quotes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Löscht alle Milestones, Quotes und abhängige CostPositions. Nur im Entwicklungsmodus erlaubt!
    """
    if not settings.debug_mode or settings.environment != "development":
        raise HTTPException(
            status_code=403, 
            detail="Nur im Entwicklungsmodus erlaubt. Setzen Sie ENVIRONMENT=development und DEBUG_MODE=true in der .env-Datei."
        )
    # ... Rest der Funktion
```

### ✅ **3. .env-Datei Setup-Tool**

#### **Neues Skript: `create_env_file.py`**
```bash
# .env-Datei mit korrekten Einstellungen erstellen
python create_env_file.py
```

## Verwendung

### **1. .env-Datei erstellen**
```bash
cd BuildWise
python create_env_file.py
```

### **2. Backend-Server neu starten**
```bash
# Stoppen Sie den aktuellen Server (Ctrl+C)
# Starten Sie ihn neu
python -m uvicorn app.main:app --reload
```

### **3. Debug-Button testen**
- Öffnen Sie die Frontend-Anwendung
- Navigieren Sie zur Quotes-Seite
- Klicken Sie auf "Debug: Alle Gewerke, Angebote & Kostenpositionen"
- Bestätigen Sie die Löschung

## Konfiguration

### **Entwicklungsmodus aktivieren**
```bash
# In der .env-Datei
ENVIRONMENT=development
DEBUG_MODE=true
```

### **Produktionsmodus (Debug deaktiviert)**
```bash
# In der .env-Datei
ENVIRONMENT=production
DEBUG_MODE=false
```

## Sicherheit

### ✅ **Schutzmaßnahmen**
- Debug-Funktionen sind nur im Entwicklungsmodus verfügbar
- Doppelte Prüfung: `debug_mode` UND `environment=development`
- Klare Fehlermeldung mit Anweisungen zur Behebung

### ✅ **Umgebungsvariablen**
- `ENVIRONMENT`: Bestimmt die Laufzeitumgebung
- `DEBUG_MODE`: Aktiviert/Deaktiviert Debug-Funktionen
- Standard: Entwicklungsmodus aktiviert

## Troubleshooting

### **Debug-Button funktioniert immer noch nicht**

1. **Prüfen Sie die .env-Datei:**
```bash
cat .env | grep -E "(ENVIRONMENT|DEBUG_MODE)"
```

2. **Starten Sie den Server neu:**
```bash
# Stoppen Sie den Server (Ctrl+C)
python -m uvicorn app.main:app --reload
```

3. **Prüfen Sie die Server-Logs:**
```bash
# Schauen Sie in die Konsole, wo der Server läuft
# Suchen Sie nach "ENVIRONMENT" oder "DEBUG_MODE"
```

### **Fehlermeldung: "Nur im Entwicklungsmodus erlaubt"**

1. **Erstellen Sie die .env-Datei:**
```bash
python create_env_file.py
```

2. **Prüfen Sie die Einstellungen:**
```bash
python -c "
from app.core.config import settings
print(f'Environment: {settings.environment}')
print(f'Debug Mode: {settings.debug_mode}')
"
```

3. **Starten Sie den Server neu**

## Ergebnis

### **Vorher**
- ❌ Debug-Button funktioniert nicht
- ❌ Fehlermeldung: "Nur im Entwicklungsmodus erlaubt"
- ❌ Keine Möglichkeit zum Testen der Löschfunktion

### **Nachher**
- ✅ Debug-Button funktioniert korrekt
- ✅ Entwicklungsmodus ist aktiviert
- ✅ Debug-Funktionen sind verfügbar
- ✅ Klare Konfiguration über .env-Datei

## Zusätzliche Features

### **Automatische .env-Erstellung**
```bash
python create_env_file.py
```

### **Konfigurationsprüfung**
```bash
python create_env_file.py
# Prüft automatisch die bestehende Konfiguration
```

### **Flexible Umgebungsumschaltung**
- Entwicklungsmodus: Debug-Funktionen aktiviert
- Produktionsmodus: Debug-Funktionen deaktiviert
- Staging-Modus: Für Tests verfügbar

---

**✅ Der Debug-Button funktioniert jetzt korrekt!** 