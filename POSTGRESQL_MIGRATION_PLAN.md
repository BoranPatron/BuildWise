
# PostgreSQL Migrationsplan für BuildWise

## Aktuelle Datenbank
- Typ: SQLite
- Datei: buildwise.db
- Tabellen: 13

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
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
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
