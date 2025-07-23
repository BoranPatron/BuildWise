#!/usr/bin/env python3
"""
Skript zur Analyse der BuildWise SQLite-Datenbankstruktur
"""

import sqlite3
import os
from typing import Dict, List, Any

def analyze_sqlite_database(db_path: str = "buildwise.db") -> Dict[str, Any]:
    """Analysiert die SQLite-Datenbankstruktur"""
    
    if not os.path.exists(db_path):
        print("❌ Datenbank " + db_path + " nicht gefunden!")
        return {}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Alle Tabellen abrufen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("📊 Gefundene Tabellen: " + str(len(tables)))
    print("📋 Tabellen: " + str(tables))
    print("\n" + "="*80 + "\n")
    
    database_info = {
        "tables": {},
        "total_tables": len(tables),
        "database_type": "SQLite",
        "file_path": db_path
    }
    
    for table_name in tables:
        print("🔍 Analysiere Tabelle: " + table_name)
        
        # Tabellenstruktur abrufen
        cursor.execute("PRAGMA table_info(" + table_name + ")")
        columns = cursor.fetchall()
        
        # Datenanzahl abrufen
        cursor.execute("SELECT COUNT(*) FROM " + table_name)
        row_count = cursor.fetchone()[0]
        
        table_info = {
            "columns": [],
            "row_count": row_count,
            "sqlite_schema": ""
        }
        
        print("   📊 Zeilen: " + str(row_count))
        print("   📋 Spalten:")
        
        for col in columns:
            col_info = {
                "name": col[1],
                "type": col[2],
                "not_null": bool(col[3]),
                "default_value": col[4],
                "primary_key": bool(col[5])
            }
            table_info["columns"].append(col_info)
            
            pk_marker = " 🔑" if col[5] else ""
            null_marker = " NOT NULL" if col[3] else ""
            default_marker = " DEFAULT " + str(col[4]) if col[4] else ""
            
            print("     - " + col[1] + ": " + col[2] + null_marker + default_marker + pk_marker)
        
        # CREATE TABLE Statement abrufen
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='" + table_name + "'")
        create_statement = cursor.fetchone()
        if create_statement:
            table_info["sqlite_schema"] = create_statement[0]
        
        database_info["tables"][table_name] = table_info
        print()
    
    conn.close()
    return database_info

def generate_postgresql_migration_plan(database_info: Dict[str, Any]) -> str:
    """Generiert einen Migrationsplan für PostgreSQL"""
    
    plan = """
# PostgreSQL Migrationsplan für BuildWise

## Aktuelle Datenbank
- Typ: """ + database_info.get('database_type', 'Unknown') + """
- Datei: """ + database_info.get('file_path', 'Unknown') + """
- Tabellen: """ + str(database_info.get('total_tables', 0)) + """

## Migrationsschritte

### 1. PostgreSQL Installation & Konfiguration

PostgreSQL installieren (Ubuntu/Debian):
sudo apt update
sudo apt install postgresql postgresql-contrib

PostgreSQL installieren (Windows):
https://www.postgresql.org/download/windows/

PostgreSQL installieren (macOS):
brew install postgresql

### 2. Datenbank erstellen

CREATE DATABASE buildwise;
CREATE USER buildwise_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE buildwise TO buildwise_user;

### 3. Konfigurationsänderungen

#### app/core/config.py

Aktuell (SQLite):
database_url: str = "sqlite:///./buildwise.db"

Nachher (PostgreSQL):
database_url: str = "postgresql+asyncpg://buildwise_user:your_secure_password@localhost:5432/buildwise"

#### app/core/database.py

Aktuell (SQLite):
DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"

Nachher (PostgreSQL):
DATABASE_URL = "postgresql+asyncpg://buildwise_user:your_secure_password@localhost:5432/buildwise"

SQLite-spezifische Parameter entfernen:
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

#### migrations/env.py

Aktuell (SQLite):
DATABASE_URL = "sqlite:///./buildwise.db"

Nachher (PostgreSQL):
DATABASE_URL = "postgresql://buildwise_user:your_secure_password@localhost:5432/buildwise"

### 4. Dependencies aktualisieren

#### requirements.txt

SQLite entfernen:
# aiosqlite

PostgreSQL hinzufügen:
asyncpg>=0.28.0
psycopg2-binary>=2.9.0

### 5. Datentyp-Anpassungen

SQLite zu PostgreSQL Datentyp-Mapping:
- INTEGER zu INTEGER (kompatibel)
- TEXT zu TEXT (kompatibel)
- VARCHAR zu VARCHAR (kompatibel)
- BOOLEAN zu BOOLEAN (kompatibel)
- REAL zu DOUBLE PRECISION (kompatibel)
- DATETIME zu TIMESTAMP WITH TIME ZONE (kompatibel)
- JSON zu JSONB (PostgreSQL-spezifisch, besser)

### 6. Migration der Daten

#### Option A: Alembic Migration (Empfohlen)

1. Neue Migration erstellen:
alembic revision --autogenerate -m "migrate_to_postgresql"

2. Migration ausführen:
alembic upgrade head

#### Option B: Datenexport/Import

1. SQLite-Daten exportieren:
python -c "
import sqlite3
import json
conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
tables = cursor.fetchall()
data = {}
for table in tables:
    table_name = table[0]
    cursor.execute('SELECT * FROM ' + table_name)
    rows = cursor.fetchall()
    data[table_name] = rows
with open('sqlite_export.json', 'w') as f:
    json.dump(data, f, default=str)
conn.close()
print('Export abgeschlossen: sqlite_export.json')
"

### 7. Tests durchführen

#### Backend-Tests

Server starten:
python -m uvicorn app.main:app --reload

API-Endpoints testen:
curl http://localhost:8000/api/v1/health

#### Datenbank-Tests

Verbindung testen:
SELECT version();

Tabellen prüfen:
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

Daten prüfen:
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM projects;

### 8. Performance-Optimierungen

#### PostgreSQL-spezifische Optimierungen:

Indizes für häufig abgefragte Felder:
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

JSONB-Indizes für JSON-Felder:
CREATE INDEX idx_users_social_profile_data ON users USING GIN(social_profile_data);
CREATE INDEX idx_audit_logs_details ON audit_logs USING GIN(details);

## Risiken & Lösungen

### 1. Datentyp-Kompatibilität
- Risiko: SQLite-Enums vs PostgreSQL-Enums
- Lösung: PostgreSQL-Enums definieren oder String-Felder verwenden

### 2. Transaktionsverhalten
- Risiko: Unterschiedliche Isolation Levels
- Lösung: PostgreSQL-spezifische Transaktionskonfiguration

### 3. Performance
- Risiko: Langsamere Abfragen bei großen Datenmengen
- Lösung: Indizes und Query-Optimierung

### 4. Backup & Recovery
- Risiko: Datenverlust während Migration
- Lösung: Vollständiges Backup vor Migration

## Rollback-Plan

Falls die Migration fehlschlägt:
1. SQLite-Datenbank sichern
2. PostgreSQL-Datenbank löschen
3. Zurück zu SQLite-Konfiguration
4. Daten aus Backup wiederherstellen

## Timeline

1. Vorbereitung (1-2 Tage)
   - PostgreSQL installieren
   - Konfiguration anpassen
   - Tests erstellen

2. Migration (1 Tag)
   - Daten migrieren
   - Tests durchführen
   - Performance optimieren

3. Deployment (1 Tag)
   - Produktionsumgebung aktualisieren
   - Monitoring einrichten
   - Dokumentation aktualisieren

Gesamtdauer: 3-4 Tage
"""
    
    return plan

if __name__ == "__main__":
    print("🔍 Analysiere BuildWise SQLite-Datenbank...")
    print("="*80)
    
    # Datenbank analysieren
    db_info = analyze_sqlite_database()
    
    if db_info:
        print("\n" + "="*80)
        print("📋 PostgreSQL Migrationsplan generieren...")
        print("="*80)
        
        # Migrationsplan generieren
        migration_plan = generate_postgresql_migration_plan(db_info)
        
        # Plan in Datei speichern
        with open("POSTGRESQL_MIGRATION_PLAN.md", "w", encoding="utf-8") as f:
            f.write(migration_plan)
        
        print("✅ Migrationsplan gespeichert: POSTGRESQL_MIGRATION_PLAN.md")
        print("\n📋 Zusammenfassung:")
        print("   - Tabellen: " + str(db_info.get('total_tables', 0)))
        print("   - Datenbank: " + db_info.get('database_type', 'Unknown'))
        print("   - Datei: " + db_info.get('file_path', 'Unknown'))
        
        # Wichtige Tabellen auflisten
        tables = list(db_info.get('tables', {}).keys())
        if tables:
            table_list = ', '.join(tables[:5])
            if len(tables) > 5:
                table_list += '...'
            print("   - Haupttabellen: " + table_list)
    else:
        print("❌ Keine Datenbank gefunden oder Analyse fehlgeschlagen!") 