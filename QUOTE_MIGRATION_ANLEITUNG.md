# 🔧 Quote-Tabelle Migration - Anleitung

## 📋 Problem
Die `quotes`-Tabelle in der buildwise.db enthielt nicht alle Felder, die über das CostEstimateForm eingegeben werden können. Viele wichtige Informationen gingen verloren.

## ✅ Lösung
Vollständige Erweiterung der Datenbank-Struktur, API-Schemas und Migration.

## 🚀 Ausführung der Migration

### 1. Backup erstellen (WICHTIG!)
```bash
# Erstelle ein Backup der Datenbank
cp buildwise.db buildwise_backup_$(date +%Y%m%d_%H%M%S).db
```

### 2. Migration ausführen
```bash
# Option A: Python-Skript (empfohlen)
cd BuildWise
python run_quote_migration.py

# Option B: Manuell mit SQL
sqlite3 buildwise.db < migration_add_quote_fields.sql
```

### 3. Anwendung neu starten
```bash
# Backend neu starten für Schema-Updates
uvicorn app.main:app --reload
```

## 📊 Hinzugefügte Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `quote_number` | VARCHAR(255) | Eindeutige Angebotsnummer |
| `qualifications` | TEXT | Qualifikationen & Zertifizierungen |
| `references` | TEXT | Referenzprojekte |
| `certifications` | TEXT | Spezifische Zertifizierungen |
| `technical_approach` | TEXT | Technischer Ansatz |
| `quality_standards` | TEXT | Qualitätsstandards |
| `safety_measures` | TEXT | Sicherheitsmaßnahmen |
| `environmental_compliance` | TEXT | Umweltschutz-Maßnahmen |
| `risk_assessment` | TEXT | Risikobewertung |
| `contingency_plan` | TEXT | Notfallpläne |
| `additional_notes` | TEXT | Zusätzliche Anmerkungen |

## 🔍 Verifikation

### Prüfe die Tabellen-Struktur:
```sql
-- SQLite
.schema quotes

-- PostgreSQL  
\d quotes
```

### Teste ein neues Angebot:
1. Öffne das CostEstimateForm
2. Fülle alle Felder aus (inklusive technische Details)
3. Reiche das Angebot ein
4. Prüfe in der Datenbank: `SELECT * FROM quotes ORDER BY id DESC LIMIT 1;`

## ⚠️ Wichtige Hinweise

- **Backup**: Immer vor Migration ein Backup erstellen!
- **Downtime**: Kurze Downtime während der Migration einplanen
- **Testing**: Nach Migration alle Funktionen testen
- **Rollback**: Bei Problemen Backup wiederherstellen

## 🐛 Troubleshooting

### Migration schlägt fehl:
```bash
# Prüfe Datenbankverbindung
python -c "from app.core.database import get_db_engine; print('DB OK')"

# Prüfe bestehende Spalten
sqlite3 buildwise.db "PRAGMA table_info(quotes);"
```

### API-Fehler nach Migration:
```bash
# Starte Backend neu
pkill -f uvicorn
uvicorn app.main:app --reload
```

## 📈 Erwartete Verbesserungen

- ✅ **Vollständige Datenspeicherung**: Alle CostEstimateForm-Felder werden gespeichert
- ✅ **Bessere Angebots-Qualität**: Detailliertere Informationen verfügbar
- ✅ **Erweiterte Filterung**: Suche nach technischen Kriterien möglich
- ✅ **Compliance-Tracking**: Sicherheits- und Umweltmaßnahmen dokumentiert
- ✅ **Risiko-Management**: Risikobewertungen und Notfallpläne erfasst

## 📞 Support
Bei Problemen: Prüfe die Logs und erstelle ein GitHub Issue mit Details zur Fehlermeldung.
