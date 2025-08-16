# BuildWise Database Reset Tools

Automatische Tools zum Zurücksetzen der BuildWise-Datenbank ohne Benutzerabfrage.

## 📁 Verfügbare Skripte

| Skript | Beschreibung | Plattform |
|--------|-------------|-----------|
| `reset_database_auto.py` | Haupt-Python-Skript mit allen Funktionen | Alle |
| `reset_db.bat` | Einfaches Windows Batch-Skript | Windows |
| `reset_db.ps1` | Erweiterte PowerShell-Version | Windows |

## 🚀 Schnellstart

### Einfachster Weg (Windows):
```bash
# Doppelklick auf reset_db.bat
# ODER
reset_db.bat
```

### Python direkt:
```bash
python reset_database_auto.py
```

### PowerShell (erweitert):
```powershell
.\reset_db.ps1
```

## ⚙️ Optionen

### Standard-Reset
Erstellt eine jungfräuliche Datenbank mit Admin-User:
```bash
python reset_database_auto.py
# Erstellt: admin@buildwise.local / Admin123!ChangeMe
```

### Ohne Admin-User
```bash
python reset_database_auto.py --no-admin
```

### Mit Storage-Bereinigung
```bash
python reset_database_auto.py --clean-storage
```

### Vollständiger Reset
```bash
python reset_database_auto.py --full-reset
# Equivalent zu: --clean-storage + Standard-Reset
```

### Struktur komplett neu erstellen
```bash
python reset_database_auto.py --recreate-structure
# ⚠️ Löscht auch die Tabellen-Struktur!
```

### Mit Backup
```bash
python reset_database_auto.py --backup
# Erstellt buildwise_backup_YYYYMMDD_HHMMSS.db
```

### Quiet Mode
```bash
python reset_database_auto.py --quiet
# Minimale Ausgaben
```

## 🔧 Was passiert beim Reset?

### 1. Standard-Reset (Struktur erhalten)
- ✅ **Behält Datenbank-Struktur bei** (Tabellen, Indizes, Constraints)
- ✅ **Löscht nur die Daten** aus allen Tabellen
- ✅ Wendet VACUUM für Optimierung an
- ✅ Erstellt optional Admin-User

### 2. Struktur-Reset (--recreate-structure)
- ⚠️ Löscht `buildwise.db` komplett
- ⚠️ Erstellt alle Tabellen neu via SQLAlchemy
- ✅ Wendet SQLite-Optimierungen an
- ✅ Erstellt optional Admin-User

### 2. Storage-Bereinigung (optional)
- 🧹 Entfernt alle Dateien aus `./storage/`
- 🧹 Entfernt leere Unterordner
- 🧹 Behält das Hauptverzeichnis `storage/`

### 3. Admin-User (Standard)
- 👤 **E-Mail:** `admin@buildwise.local`
- 🔑 **Passwort:** `Admin123!ChangeMe`
- ⚠️ **Wichtig:** Passwort nach erstem Login ändern!

## 🛡️ Sicherheit

### Automatische Ausführung
- ✅ **Keine Bestätigung erforderlich** (im Gegensatz zum ursprünglichen Skript)
- ✅ Arbeitsverzeichnis-Prüfung (muss BuildWise-Root sein)
- ✅ Backup-Option verfügbar
- ✅ Fehlerbehandlung und Rollback

### Backup-Empfehlung
```bash
# Immer mit Backup für Produktionsdaten
python reset_database_auto.py --backup
```

## 🔍 Troubleshooting

### "Python nicht gefunden"
```bash
# Python installieren oder PATH prüfen
python --version
```

### "Nicht im BuildWise-Verzeichnis"
```bash
# Ins richtige Verzeichnis wechseln
cd C:\Users\user\Documents\04_Repo\BuildWise
python reset_database_auto.py
```

### "Module nicht gefunden"
```bash
# Virtual Environment aktivieren (falls verwendet)
# Oder Dependencies installieren
pip install -r requirements.txt
```

### PowerShell Execution Policy
```powershell
# Falls PowerShell-Skript blockiert wird
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📊 Vergleich der Skripte

| Feature | Python | Batch | PowerShell |
|---------|--------|-------|------------|
| Alle Optionen | ✅ | ❌ | ✅ |
| Fehlerbehandlung | ✅ | ⚠️ | ✅ |
| Farbige Ausgabe | ✅ | ❌ | ✅ |
| Hilfe-System | ✅ | ❌ | ✅ |
| Plattform | Alle | Windows | Windows |
| Einfachheit | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## 🎯 Empfohlene Verwendung

### Entwicklung (täglich)
```bash
reset_db.bat
# Oder einfach Doppelklick
```

### Testing/CI
```bash
python reset_database_auto.py --quiet --no-admin
```

### Produktion (Vorsicht!)
```bash
python reset_database_auto.py --backup --full-reset
```

### Debugging
```bash
python reset_database_auto.py --backup
# Dann bei Problemen: Backup wiederherstellen
```

## 🔄 Migration vom alten Skript

### Vorher (mit Bestätigung):
```bash
RESET_CONFIRM=YES python reset_database.py
```

### Nachher (automatisch):
```bash
python reset_database_auto.py
# Oder einfach:
reset_db.bat
```

## 📝 Logs und Ausgaben

### Standard-Ausgabe (Struktur erhalten)
```
============================================================
🔄 BuildWise Database Auto-Reset
============================================================
📍 Arbeitsverzeichnis: C:\Users\user\Documents\04_Repo\BuildWise
🎯 Datenbank-Pfad: C:\Users\user\Documents\04_Repo\BuildWise\buildwise.db
🧹 Lösche alle Daten (Struktur bleibt erhalten)...
   🗑️  users: 5 Einträge gelöscht
   🗑️  projects: 12 Einträge gelöscht
   🗑️  quotes: 8 Einträge gelöscht
✅ Insgesamt 25 Einträge aus 15 Tabellen gelöscht
⚡ SQLite-Optimierungen angewendet
👤 Admin-User erstellt:
   📧 E-Mail: admin@buildwise.local
   🔑 Passwort: Admin123!ChangeMe
   ⚠️  Bitte Passwort nach dem ersten Login ändern!
============================================================
🎉 BuildWise Datenbank erfolgreich zurückgesetzt!
============================================================
👤 Admin-Login: admin@buildwise.local / Admin123!ChangeMe
🚀 Die Anwendung kann jetzt gestartet werden.
```

### Quiet-Mode
```
Database reset completed successfully.
```

---

**✨ Jetzt haben Sie eine jungfräuliche BuildWise-Datenbank ohne lästige Bestätigungen!**
