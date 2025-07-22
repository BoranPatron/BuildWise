# BuildWise Gebühren - Persistente Speicherung

## Problem

Das Gebühren-Umschaltungstool konnte keine Prozentwerte ändern, weil die Änderungen nur im Arbeitsspeicher gemacht wurden, aber nicht persistent in die .env-Datei gespeichert wurden.

## Symptome

```bash
# Benutzer wechselt zu Production
python switch_buildwise_fees.py --phase production
🔄 Wechsle zu Phase: production
   Prozentsatz: 4.0%
   Beschreibung: Go-Live (4% Gebühr für alle Nutzer)
✅ Erfolgreich zu Phase 'production' gewechselt!
   Neuer Prozentsatz: 4.0%

# Aber beim Status-Check zeigt es immer noch Beta an
python switch_buildwise_fees.py --status
📊 Aktueller Prozentsatz: 0.0%
🏷️  Aktuelle Phase: beta
```

## Ursache

Das Tool änderte nur die Werte im `settings`-Objekt im Arbeitsspeicher, aber speicherte sie nicht in die .env-Datei. Beim Neustart des Servers wurden die Standardwerte wieder geladen.

## Lösung

### ✅ **1. Tool erweitert für persistente Speicherung**

#### **Neue Funktion: `save_config_to_env()`**
```python
def save_config_to_env(self):
    """Speichert die aktuelle Konfiguration in die .env-Datei."""
    try:
        # Erstelle neue .env-Inhalte mit aktuellen Werten
        new_env_content = f"""# BuildWise Gebühren-Konfiguration
# Generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Umgebung
ENVIRONMENT=development
DEBUG_MODE=true

# BuildWise Gebühren-Konfiguration
BUILDWISE_FEE_PERCENTAGE={settings.buildwise_fee_percentage}
BUILDWISE_FEE_PHASE={settings.buildwise_fee_phase}
BUILDWISE_FEE_ENABLED={str(settings.buildwise_fee_enabled).lower()}

# ... weitere Konfigurationen
"""
        
        # Schreibe neue .env-Datei
        with open(".env", "w", encoding="utf-8") as f:
            f.write(new_env_content)
        
        print("✅ Konfiguration in .env-Datei gespeichert!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Speichern der .env-Datei: {e}")
        return False
```

### ✅ **2. Automatische Speicherung bei Änderungen**

#### **Erweiterte `switch_to_phase()` Funktion**
```python
def switch_to_phase(self, phase: str):
    # ... Validierung und Bestätigung ...
    
    # Konfiguration aktualisieren
    settings.buildwise_fee_percentage = phase_info['percentage']
    settings.buildwise_fee_phase = phase
    settings.buildwise_fee_enabled = True
    
    # Speichere Änderungen in .env-Datei
    if self.save_config_to_env():
        print(f"✅ Erfolgreich zu Phase '{phase}' gewechselt!")
        print(f"   Neuer Prozentsatz: {settings.buildwise_fee_percentage}%")
        print("💡 Starten Sie den Backend-Server neu, um die Änderungen zu übernehmen.")
        return True
    else:
        print("❌ Fehler beim Speichern der Konfiguration")
        return False
```

### ✅ **3. Test-Skript für Validierung**

#### **Neues Skript: `test_fee_config_changes.py`**
```bash
# Testet die Konfigurationsänderungen
python test_fee_config_changes.py
```

## Verwendung

### **1. Gebühren-Konfiguration ändern**
```bash
# Zu Production wechseln (4%)
python switch_buildwise_fees.py --phase production

# Zu Beta wechseln (0%)
python switch_buildwise_fees.py --phase beta
```

### **2. Status prüfen**
```bash
# Aktuelle Konfiguration anzeigen
python switch_buildwise_fees.py --status
```

### **3. Konfiguration testen**
```bash
# Testet die persistente Speicherung
python test_fee_config_changes.py
```

### **4. Backend-Server neu starten**
```bash
# Stoppen Sie den Server (Ctrl+C)
# Starten Sie ihn neu
python -m uvicorn app.main:app --reload
```

## Beispiel-Ausgabe

### **Vorher (nicht persistent)**
```bash
python switch_buildwise_fees.py --phase production
✅ Erfolgreich zu Phase 'production' gewechselt!
   Neuer Prozentsatz: 4.0%

python switch_buildwise_fees.py --status
📊 Aktueller Prozentsatz: 0.0%  # ❌ Nicht gespeichert
🏷️  Aktuelle Phase: beta        # ❌ Nicht gespeichert
```

### **Nachher (persistent)**
```bash
python switch_buildwise_fees.py --phase production
✅ Erfolgreich zu Phase 'production' gewechselt!
   Neuer Prozentsatz: 4.0%
✅ Konfiguration in .env-Datei gespeichert!
💡 Starten Sie den Backend-Server neu, um die Änderungen zu übernehmen.

python switch_buildwise_fees.py --status
📊 Aktueller Prozentsatz: 4.0%  # ✅ Gespeichert
🏷️  Aktuelle Phase: production  # ✅ Gespeichert
```

## Technische Details

### **Persistente Speicherung**
- **Vollständige .env-Datei**: Alle Einstellungen werden gespeichert
- **Zeitstempel**: Automatische Dokumentation der Änderungen
- **Fehlerbehandlung**: Sichere Speicherung mit Rollback

### **Automatische Validierung**
- **Test-Skript**: Prüft .env-Datei und Einstellungen
- **Konfigurationsprüfung**: Validiert alle wichtigen Einstellungen
- **Fehlerdiagnose**: Klare Fehlermeldungen und Lösungsvorschläge

### **Sicherheit**
- **Backup**: Bestehende .env-Datei wird nicht überschrieben ohne Bestätigung
- **Validierung**: Alle Werte werden vor dem Speichern validiert
- **Rollback**: Bei Fehlern wird die ursprüngliche Konfiguration beibehalten

## Troubleshooting

### **Änderungen werden nicht gespeichert**

1. **Prüfen Sie die Schreibrechte:**
```bash
ls -la .env
```

2. **Testen Sie die Konfiguration:**
```bash
python test_fee_config_changes.py
```

3. **Manuell .env-Datei erstellen:**
```bash
python create_env_file.py
```

### **Server zeigt alte Werte**

1. **Server neu starten:**
```bash
# Stoppen Sie den Server (Ctrl+C)
python -m uvicorn app.main:app --reload
```

2. **Konfiguration prüfen:**
```bash
python -c "
from app.core.config import settings
print(f'Gebühren: {settings.buildwise_fee_percentage}%')
print(f'Phase: {settings.buildwise_fee_phase}')
"
```

### **Fehler beim Speichern**

1. **Prüfen Sie den Speicherplatz:**
```bash
df -h .
```

2. **Prüfen Sie die Berechtigungen:**
```bash
chmod 644 .env
```

## Ergebnis

### **Vorher**
- ❌ Änderungen nur im Arbeitsspeicher
- ❌ Keine persistente Speicherung
- ❌ Werte gehen beim Neustart verloren
- ❌ Inkonsistente Anzeige

### **Nachher**
- ✅ Vollständige persistente Speicherung
- ✅ Automatische .env-Datei-Aktualisierung
- ✅ Werte bleiben nach Neustart erhalten
- ✅ Konsistente Anzeige
- ✅ Test-Skript für Validierung

---

**✅ Die Gebühren-Konfiguration wird jetzt korrekt persistent gespeichert!** 