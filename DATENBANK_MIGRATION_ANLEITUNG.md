# Datenbank-Migration für Bauphasen-Funktionalität

## Übersicht

Diese Anleitung beschreibt die notwendigen Schritte zur Migration der Datenbank für die Bauphasen-Funktionalität.

## 🔍 Voraussetzungen

### Erforderliche Dateien
- ✅ `buildwise.db` - SQLite-Datenbank
- ✅ `add_construction_phase_migration.py` - Migration-Skript
- ✅ `check_database_construction_phases.py` - Überprüfungs-Skript

### Datenbank-Struktur
Die Migration fügt folgende Spalten zur `projects` Tabelle hinzu:

1. **`construction_phase`** (TEXT, nullable)
   - Speichert die aktuelle Bauphase des Projekts
   - Beispiele: "rohbau", "fundament", "fertigstellung"

2. **`address_country`** (TEXT, nullable, DEFAULT 'Deutschland')
   - Speichert das Land des Projekts
   - Beispiele: "Deutschland", "Schweiz", "Österreich"

## 🚀 Migration durchführen

### Schritt 1: Überprüfung der aktuellen Struktur

```bash
# Überprüfe die aktuelle Datenbank-Struktur
python check_database_construction_phases.py
```

**Erwartete Ausgabe:**
```
🔍 Bauphasen-Datenbank-Überprüfung
==================================================

📋 Aktuelle Spalten in projects Tabelle:
  - id (INTEGER) NOT NULL
  - owner_id (INTEGER)
  - name (TEXT) NOT NULL
  - description (TEXT)
  - project_type (TEXT) NOT NULL
  - status (TEXT) NOT NULL
  - address (TEXT)
  - address_street (TEXT)
  - address_zip (TEXT)
  - address_city (TEXT)
  - address_country (TEXT)
  - address_latitude (REAL)
  - address_longitude (REAL)
  - address_geocoded (INTEGER)
  - address_geocoding_date (TEXT)
  - property_size (REAL)
  - construction_area (REAL)
  - start_date (TEXT)
  - end_date (TEXT)
  - estimated_duration (INTEGER)
  - budget (REAL)
  - current_costs (REAL)
  - progress_percentage (REAL)
  - is_public (INTEGER)
  - allow_quotes (INTEGER)
  - construction_phase (TEXT)
  - created_at (TEXT)
  - updated_at (TEXT)

✅ Alle erforderlichen Spalten für Bauphasen vorhanden!
```

### Schritt 2: Migration ausführen

```bash
# Führe die Migration aus
python add_construction_phase_migration.py
```

**Erwartete Ausgabe:**
```
🏗️ Bauphasen-Datenbank-Migration
==================================================

1️⃣ Überprüfe Datenbank-Struktur...
📋 Aktuelle Spalten in projects Tabelle:
  - id (INTEGER) NOT NULL
  - owner_id (INTEGER)
  - name (TEXT) NOT NULL
  - description (TEXT)
  - project_type (TEXT) NOT NULL
  - status (TEXT) NOT NULL
  - address (TEXT)
  - address_street (TEXT)
  - address_zip (TEXT)
  - address_city (TEXT)
  - address_country (TEXT)
  - address_latitude (REAL)
  - address_longitude (REAL)
  - address_geocoded (INTEGER)
  - address_geocoding_date (TEXT)
  - property_size (REAL)
  - construction_area (REAL)
  - start_date (TEXT)
  - end_date (TEXT)
  - estimated_duration (INTEGER)
  - budget (REAL)
  - current_costs (REAL)
  - progress_percentage (REAL)
  - is_public (INTEGER)
  - allow_quotes (INTEGER)
  - construction_phase (TEXT)
  - created_at (TEXT)
  - updated_at (TEXT)

2️⃣ Füge Bauphasen-Spalten hinzu...
✅ construction_phase Spalte bereits vorhanden
✅ address_country Spalte bereits vorhanden
ℹ️ Keine Änderungen erforderlich - alle Spalten bereits vorhanden

3️⃣ Aktualisiere bestehende Projekte...
ℹ️ Alle Projekte haben bereits ein Land gesetzt

4️⃣ Überprüfe Migration...
✅ Alle erforderlichen Spalten vorhanden:
  - construction_phase
  - address_country
📊 Anzahl Projekte in der Datenbank: 5
🌍 Länder-Verteilung:
  - Deutschland: 5 Projekte

🎉 Migration erfolgreich abgeschlossen!
✅ Die Datenbank ist bereit für die Bauphasen-Funktionalität

📋 Nächste Schritte:
  1. Starten Sie den Backend-Server neu
  2. Testen Sie die Bauphasen-Funktionalität im Frontend
  3. Erstellen Sie ein neues Projekt mit Bauphasen
```

### Schritt 3: Verifikation

```bash
# Überprüfe die Migration erneut
python check_database_construction_phases.py
```

## 🔧 Manuelle Migration (falls automatische Migration fehlschlägt)

### SQL-Befehle für manuelle Migration

```sql
-- 1. Füge construction_phase Spalte hinzu
ALTER TABLE projects ADD COLUMN construction_phase TEXT;

-- 2. Füge address_country Spalte hinzu
ALTER TABLE projects ADD COLUMN address_country TEXT DEFAULT 'Deutschland';

-- 3. Aktualisiere bestehende Projekte
UPDATE projects SET address_country = 'Deutschland' WHERE address_country IS NULL OR address_country = '';

-- 4. Überprüfe die Änderungen
PRAGMA table_info(projects);
SELECT COUNT(*) FROM projects;
SELECT address_country, COUNT(*) FROM projects GROUP BY address_country;
```

### SQLite-Befehle ausführen

```bash
# Öffne SQLite-Konsole
sqlite3 buildwise.db

# Führe die SQL-Befehle aus
ALTER TABLE projects ADD COLUMN construction_phase TEXT;
ALTER TABLE projects ADD COLUMN address_country TEXT DEFAULT 'Deutschland';
UPDATE projects SET address_country = 'Deutschland' WHERE address_country IS NULL OR address_country = '';

# Überprüfe die Änderungen
PRAGMA table_info(projects);
SELECT COUNT(*) FROM projects;
SELECT address_country, COUNT(*) FROM projects GROUP BY address_country;

# Verlasse SQLite
.quit
```

## 🧪 Testen der Migration

### Test-Skript ausführen

```bash
python check_database_construction_phases.py
```

### Erwartete Testergebnisse

```
🔍 Bauphasen-Datenbank-Überprüfung
==================================================

📋 Aktuelle Spalten in projects Tabelle:
  - id (INTEGER) NOT NULL
  - owner_id (INTEGER)
  - name (TEXT) NOT NULL
  - description (TEXT)
  - project_type (TEXT) NOT NULL
  - status (TEXT) NOT NULL
  - address (TEXT)
  - address_street (TEXT)
  - address_zip (TEXT)
  - address_city (TEXT)
  - address_country (TEXT)
  - address_latitude (REAL)
  - address_longitude (REAL)
  - address_geocoded (INTEGER)
  - address_geocoding_date (TEXT)
  - property_size (REAL)
  - construction_area (REAL)
  - start_date (TEXT)
  - end_date (TEXT)
  - estimated_duration (INTEGER)
  - budget (REAL)
  - current_costs (REAL)
  - progress_percentage (REAL)
  - is_public (INTEGER)
  - allow_quotes (INTEGER)
  - construction_phase (TEXT)
  - created_at (TEXT)
  - updated_at (TEXT)

✅ Alle erforderlichen Spalten für Bauphasen vorhanden!

📊 Projekte-Statistik:
  - Gesamt: 5 Projekte
  - Mit Bauphase: 0 Projekte
  - Mit Land: 5 Projekte

🌍 Länder-Verteilung:
  - Deutschland: 5 Projekte

🧪 Teste Bauphasen-Funktionalität...

🌍 Teste Deutschland:
  Erwartete Phasen: 10
  Phasen: planungsphase, baugenehmigung, ausschreibung...

🌍 Teste Schweiz:
  Erwartete Phasen: 11
  Phasen: vorprojekt, projektierung, baugenehmigung...

🌍 Teste Österreich:
  Erwartete Phasen: 10
  Phasen: planungsphase, einreichung, ausschreibung...

✅ Bauphasen-Tests abgeschlossen

✅ Datenbank ist bereit für Bauphasen!

🎉 Überprüfung erfolgreich abgeschlossen!
📋 Die Datenbank unterstützt alle Bauphasen-Features
```

## 🚨 Troubleshooting

### Problem 1: Datenbank nicht gefunden
```
❌ Datenbank buildwise.db nicht gefunden!
```

**Lösung:**
- Stellen Sie sicher, dass Sie sich im richtigen Verzeichnis befinden
- Überprüfen Sie, ob die Datei `buildwise.db` existiert
- Erstellen Sie die Datenbank falls nötig: `python create_tables.py`

### Problem 2: Tabelle 'projects' nicht gefunden
```
❌ Tabelle 'projects' nicht gefunden!
```

**Lösung:**
- Stellen Sie sicher, dass die Datenbank korrekt initialisiert wurde
- Führen Sie `python create_tables.py` aus
- Überprüfen Sie die Datenbank-Struktur

### Problem 3: Spalten bereits vorhanden
```
✅ construction_phase Spalte bereits vorhanden
✅ address_country Spalte bereits vorhanden
```

**Hinweis:** Das ist normal! Die Migration ist bereits durchgeführt worden.

### Problem 4: SQLite-Fehler
```
❌ Fehler bei der Migration: ...
```

**Lösung:**
- Überprüfen Sie die SQLite-Version: `sqlite3 --version`
- Stellen Sie sicher, dass die Datenbank nicht gesperrt ist
- Schließen Sie alle Verbindungen zur Datenbank
- Führen Sie die manuelle Migration aus

## 📋 Checkliste

- ✅ Datenbank `buildwise.db` existiert
- ✅ Tabelle `projects` existiert
- ✅ Spalte `construction_phase` hinzugefügt
- ✅ Spalte `address_country` hinzugefügt
- ✅ Bestehende Projekte aktualisiert
- ✅ Migration verifiziert
- ✅ Tests erfolgreich

## 🎯 Nächste Schritte

Nach erfolgreicher Migration:

1. **Backend-Server neu starten**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. **Frontend testen**
   - Öffnen Sie die Anwendung im Browser
   - Erstellen Sie ein neues Projekt
   - Wählen Sie ein Land aus
   - Testen Sie die Bauphasen-Auswahl

3. **Zeitstrahl testen**
   - Überprüfen Sie die Zeitstrahl-Darstellung im Dashboard
   - Testen Sie die responsive Darstellung auf Mobile

## 📞 Support

Bei Problemen mit der Migration:

1. Überprüfen Sie die Logs: `python check_database_construction_phases.py`
2. Führen Sie die manuelle Migration aus
3. Kontaktieren Sie das Entwicklungsteam

Die Migration ist **sicher** und **rückwärtskompatibel**! 🚀 