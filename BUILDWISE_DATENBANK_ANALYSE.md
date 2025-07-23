# BuildWise Datenbank-Analyse & PostgreSQL Migrationsplan

## 📊 Aktuelle Datenbankstruktur

### **Datenbank-Übersicht**
- **Typ**: SQLite 3.x
- **Datei**: `buildwise.db`
- **Tabellen**: 13
- **Gesamte Zeilen**: ~450 Datensätze

### **Tabellen-Details**

#### 1. **users** (7 Zeilen) - Benutzerverwaltung
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `email` (TEXT, NOT NULL, Unique)
- `first_name`, `last_name` (TEXT, NOT NULL)
- `hashed_password` (TEXT, nullable für Social-Login)
- `auth_provider` (TEXT) - EMAIL, GOOGLE, MICROSOFT
- `user_role` (TEXT) - BAUTRAEGER, DIENSTLEISTER, ADMIN
- `subscription_plan` (TEXT) - BASIS, PRO
- `subscription_status` (TEXT) - ACTIVE, INACTIVE, CANCELED, PAST_DUE

**Social-Login:**
- `google_sub`, `microsoft_sub`, `apple_sub` (TEXT)
- `social_profile_data` (TEXT/JSON)

**DSGVO-Compliance:**
- `consent_fields`, `consent_history` (TEXT/JSON)
- `data_processing_consent`, `marketing_consent` (BOOLEAN)
- `data_deletion_requested`, `data_anonymized` (BOOLEAN)
- `data_export_requested`, `data_export_token` (TEXT)

**Sicherheit:**
- `failed_login_attempts` (INTEGER)
- `account_locked_until` (DATETIME)
- `mfa_enabled`, `mfa_secret` (BOOLEAN/TEXT)

#### 2. **projects** (11 Zeilen) - Projektverwaltung
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `owner_id` (INTEGER, Foreign Key → users.id)
- `name` (VARCHAR, NOT NULL)
- `description` (TEXT)
- `project_type` (VARCHAR(13)) - NEW_BUILD, RENOVATION, EXTENSION, REFURBISHMENT
- `status` (VARCHAR(11)) - PLANNING, PREPARATION, EXECUTION, COMPLETION, COMPLETED, ON_HOLD, CANCELLED

**Geo-basierte Adresse:**
- `address`, `address_street`, `address_zip`, `address_city`, `address_country` (VARCHAR)
- `address_latitude`, `address_longitude` (FLOAT)
- `address_geocoded` (BOOLEAN)
- `address_geocoding_date` (DATETIME)

**Projektdetails:**
- `property_size`, `construction_area` (FLOAT) - in m²
- `start_date`, `end_date` (DATE)
- `estimated_duration` (INTEGER) - in Tagen
- `budget`, `current_costs` (FLOAT)
- `progress_percentage` (FLOAT)
- `construction_phase` (VARCHAR)

#### 3. **audit_logs** (407 Zeilen) - Audit-Trail
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `user_id` (INTEGER, Foreign Key → users.id)
- `session_id`, `ip_address` (VARCHAR)
- `user_agent` (TEXT)
- `action` (VARCHAR(21)) - USER_LOGIN, DATA_CREATE, DATA_UPDATE, etc.
- `resource_type`, `resource_id` (VARCHAR/INTEGER)
- `description` (TEXT)
- `details` (JSON)
- `processing_purpose`, `legal_basis` (VARCHAR)
- `risk_level` (VARCHAR)
- `requires_review` (BOOLEAN)

#### 4. **expenses** (0 Zeilen) - Ausgabenverwaltung
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `title` (VARCHAR(255), NOT NULL)
- `description` (TEXT)
- `amount` (FLOAT, NOT NULL)
- `category` (VARCHAR(50), NOT NULL) - material, labor, equipment, services, permits, other
- `project_id` (INTEGER, NOT NULL, Foreign Key → projects.id)
- `date` (DATETIME, NOT NULL)
- `receipt_url` (VARCHAR(500))

#### 5. **milestones** (11 Zeilen) - Meilensteinverwaltung
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `project_id` (INTEGER, Foreign Key → projects.id)
- `created_by` (INTEGER, Foreign Key → users.id)
- `title` (VARCHAR, NOT NULL)
- `description` (TEXT)
- `status` (VARCHAR(11)) - PLANNED, IN_PROGRESS, COMPLETED, ON_HOLD, CANCELLED
- `priority` (VARCHAR(8)) - LOW, MEDIUM, HIGH, CRITICAL
- `category` (VARCHAR)
- `planned_date`, `actual_date`, `start_date`, `end_date` (DATE)
- `budget`, `actual_costs` (FLOAT)
- `contractor` (VARCHAR)
- `progress_percentage` (INTEGER)
- `construction_phase` (TEXT)

#### 6. **quotes** (3 Zeilen) - Angebotsverwaltung
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `project_id`, `milestone_id` (INTEGER, Foreign Keys)
- `service_provider_id` (INTEGER, Foreign Key → users.id)
- `title` (VARCHAR, NOT NULL)
- `description` (TEXT)
- `status` (VARCHAR(12)) - DRAFT, SUBMITTED, ACCEPTED, REJECTED, EXPIRED
- `total_amount` (FLOAT, NOT NULL)
- `currency` (VARCHAR)
- `labor_cost`, `material_cost`, `overhead_cost` (FLOAT)
- `estimated_duration` (INTEGER)
- `start_date`, `completion_date` (DATE)
- `payment_terms`, `warranty_period` (TEXT/INTEGER)
- `risk_score`, `price_deviation` (FLOAT)
- `ai_recommendation` (VARCHAR)
- `contact_released` (BOOLEAN)
- `company_name`, `contact_person`, `phone`, `email`, `website` (VARCHAR)
- `pdf_upload_path` (VARCHAR)
- `rating`, `feedback`, `rejection_reason` (FLOAT/TEXT)

#### 7. **cost_positions** (2 Zeilen) - Kostenpositionen
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `project_id` (INTEGER, Foreign Key → projects.id)
- `title` (VARCHAR, NOT NULL)
- `description` (TEXT)
- `amount` (FLOAT, NOT NULL)
- `currency` (VARCHAR)
- `category` (VARCHAR(11)) - MATERIAL, LABOR, EQUIPMENT, SERVICES, PERMITS, OTHER
- `cost_type` (VARCHAR(14)) - FIXED, VARIABLE, RECURRING
- `status` (VARCHAR(9)) - PLANNED, ACTIVE, COMPLETED, CANCELLED
- `contractor_name`, `contractor_contact`, `contractor_phone`, `contractor_email`, `contractor_website` (VARCHAR)
- `quote_id`, `milestone_id`, `service_provider_id` (INTEGER, Foreign Keys)
- `labor_cost`, `material_cost`, `overhead_cost` (FLOAT)
- `risk_score`, `price_deviation` (FLOAT)
- `progress_percentage`, `paid_amount` (FLOAT)
- `construction_phase` (TEXT)

#### 8. **buildwise_fees** (2 Zeilen) - BuildWise Gebühren
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `project_id`, `quote_id`, `cost_position_id`, `service_provider_id` (INTEGER, NOT NULL, Foreign Keys)
- `fee_amount`, `quote_amount` (NUMERIC(10,2), NOT NULL)
- `fee_percentage` (NUMERIC(5,2), NOT NULL)
- `currency` (VARCHAR(3), NOT NULL)
- `invoice_number` (VARCHAR(50))
- `invoice_date`, `due_date`, `payment_date` (DATE)
- `status` (VARCHAR(20), NOT NULL)
- `invoice_pdf_path` (VARCHAR(255))
- `invoice_pdf_generated` (BOOLEAN)
- `tax_rate`, `tax_amount`, `net_amount`, `gross_amount` (NUMERIC)

#### 9. **documents** (7 Zeilen) - Dokumentenverwaltung
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `project_id` (INTEGER, Foreign Key → projects.id)
- `uploaded_by` (INTEGER, Foreign Key → users.id)
- `title` (VARCHAR, NOT NULL)
- `description` (TEXT)
- `document_type` (VARCHAR(8)) - PLAN, CONTRACT, INVOICE, PHOTO, OTHER
- `file_name`, `file_path` (VARCHAR, NOT NULL)
- `file_size` (INTEGER, NOT NULL)
- `mime_type` (VARCHAR, NOT NULL)
- `version`, `is_latest` (INTEGER/BOOLEAN)
- `parent_document_id` (INTEGER, Foreign Key → documents.id)
- `tags`, `category` (VARCHAR)
- `is_public`, `is_encrypted` (BOOLEAN)

#### 10. **tasks** (0 Zeilen) - Aufgabenverwaltung
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `project_id` (INTEGER, Foreign Key → projects.id)
- `assigned_to`, `created_by` (INTEGER, Foreign Keys → users.id)
- `title` (VARCHAR, NOT NULL)
- `description` (TEXT)
- `status` (VARCHAR(11)) - TODO, IN_PROGRESS, REVIEW, COMPLETED, CANCELLED
- `priority` (VARCHAR(6)) - LOW, MEDIUM, HIGH, URGENT
- `due_date` (DATE)
- `estimated_hours`, `actual_hours` (INTEGER)
- `progress_percentage` (INTEGER)
- `is_milestone` (BOOLEAN)
- `completed_at` (DATETIME)

#### 11. **messages** (0 Zeilen) - Nachrichtenverwaltung
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `project_id` (INTEGER, Foreign Key → projects.id)
- `sender_id`, `recipient_id` (INTEGER, Foreign Keys → users.id)
- `message_type` (VARCHAR(12)) - TEXT, SYSTEM, NOTIFICATION
- `content` (TEXT, NOT NULL)
- `document_id` (INTEGER, Foreign Key → documents.id)
- `is_read`, `is_system_message`, `is_encrypted` (BOOLEAN)
- `read_at` (DATETIME)

#### 12. **buildwise_fee_items** (0 Zeilen) - BuildWise Gebühren-Details
**Hauptfelder:**
- `id` (INTEGER, Primary Key)
- `buildwise_fee_id` (INTEGER, NOT NULL, Foreign Key → buildwise_fees.id)
- `quote_id`, `cost_position_id` (INTEGER, NOT NULL, Foreign Keys)
- `quote_amount`, `fee_amount` (NUMERIC(10,2), NOT NULL)
- `fee_percentage` (NUMERIC(5,2), NOT NULL)
- `description` (TEXT)

#### 13. **sqlite_sequence** (2 Zeilen) - SQLite System-Tabelle
- `name` (TEXT)
- `seq` (INTEGER)

## 🔄 PostgreSQL Migration

### **Datentyp-Mapping**

| SQLite | PostgreSQL | Kompatibilität |
|--------|------------|----------------|
| `INTEGER` | `INTEGER` | ✅ Vollständig kompatibel |
| `TEXT` | `TEXT` | ✅ Vollständig kompatibel |
| `VARCHAR(n)` | `VARCHAR(n)` | ✅ Vollständig kompatibel |
| `BOOLEAN` | `BOOLEAN` | ✅ Vollständig kompatibel |
| `FLOAT` | `DOUBLE PRECISION` | ✅ Kompatibel |
| `DATETIME` | `TIMESTAMP WITH TIME ZONE` | ✅ Kompatibel |
| `DATE` | `DATE` | ✅ Vollständig kompatibel |
| `JSON` | `JSONB` | ✅ PostgreSQL-spezifisch, besser |
| `NUMERIC(p,s)` | `NUMERIC(p,s)` | ✅ Vollständig kompatibel |

### **Besondere Herausforderungen**

#### 1. **Enum-Handling**
**Problem:** SQLite speichert Enums als VARCHAR, PostgreSQL kann native Enums verwenden
**Lösung:** 
```sql
-- PostgreSQL Enums definieren
CREATE TYPE user_type AS ENUM ('private', 'professional', 'service_provider');
CREATE TYPE project_status AS ENUM ('planning', 'preparation', 'execution', 'completion', 'completed', 'on_hold', 'cancelled');
-- etc.
```

#### 2. **JSON-Felder**
**Problem:** SQLite JSON vs PostgreSQL JSONB
**Lösung:** 
```sql
-- JSONB für bessere Performance und Indizierung
ALTER TABLE users ALTER COLUMN social_profile_data TYPE JSONB;
ALTER TABLE audit_logs ALTER COLUMN details TYPE JSONB;
```

#### 3. **Zeitzonen-Handling**
**Problem:** SQLite DATETIME vs PostgreSQL TIMESTAMP WITH TIME ZONE
**Lösung:**
```sql
-- Explizite Zeitzonen-Handhabung
ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;
ALTER TABLE projects ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;
```

### **Performance-Optimierungen**

#### **Indizes für PostgreSQL**
```sql
-- Häufig abgefragte Felder
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_auth_provider ON users(auth_provider);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- JSONB-Indizes für JSON-Felder
CREATE INDEX idx_users_social_profile_data ON users USING GIN(social_profile_data);
CREATE INDEX idx_audit_logs_details ON audit_logs USING GIN(details);

-- Composite-Indizes
CREATE INDEX idx_quotes_project_status ON quotes(project_id, status);
CREATE INDEX idx_cost_positions_project_category ON cost_positions(project_id, category);
```

#### **Partitionierung (für große Tabellen)**
```sql
-- Audit-Logs nach Datum partitionieren
CREATE TABLE audit_logs_2024 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE audit_logs_2025 PARTITION OF audit_logs
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### **Sicherheitsaspekte**

#### **Row Level Security (RLS)**
```sql
-- RLS für Projekte aktivieren
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Policy: Benutzer können nur ihre eigenen Projekte sehen
CREATE POLICY project_owner_policy ON projects
    FOR ALL USING (owner_id = current_user_id());
```

#### **Verschlüsselung**
```sql
-- Sensible Daten verschlüsseln
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Beispiel für verschlüsselte Passwörter
ALTER TABLE users ADD COLUMN encrypted_password BYTEA;
```

## 📋 Migrationsplan

### **Phase 1: Vorbereitung (1-2 Tage)**
1. **PostgreSQL Installation**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # Windows
   # https://www.postgresql.org/download/windows/
   
   # macOS
   brew install postgresql
   ```

2. **Datenbank erstellen**
   ```sql
   CREATE DATABASE buildwise;
   CREATE USER buildwise_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE buildwise TO buildwise_user;
   ```

3. **Dependencies aktualisieren**
   ```txt
   # requirements.txt
   # Entfernen: aiosqlite
   # Hinzufügen:
   asyncpg>=0.28.0
   psycopg2-binary>=2.9.0
   ```

### **Phase 2: Konfiguration (1 Tag)**
1. **app/core/config.py**
   ```python
   # ❌ Aktuell (SQLite):
   database_url: str = "sqlite:///./buildwise.db"
   
   # ✅ Nachher (PostgreSQL):
   database_url: str = "postgresql+asyncpg://buildwise_user:your_secure_password@localhost:5432/buildwise"
   ```

2. **app/core/database.py**
   ```python
   # ❌ Aktuell (SQLite):
   DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
   
   # ✅ Nachher (PostgreSQL):
   DATABASE_URL = "postgresql+asyncpg://buildwise_user:your_secure_password@localhost:5432/buildwise"
   
   # SQLite-spezifische Parameter entfernen:
   engine = create_async_engine(
       DATABASE_URL, 
       echo=False, 
       future=True,
       pool_pre_ping=True,
       pool_recycle=3600,
       pool_size=10,
       max_overflow=20
   )
   ```

3. **migrations/env.py**
   ```python
   # ❌ Aktuell (SQLite):
   DATABASE_URL = "sqlite:///./buildwise.db"
   
   # ✅ Nachher (PostgreSQL):
   DATABASE_URL = "postgresql://buildwise_user:your_secure_password@localhost:5432/buildwise"
   ```

### **Phase 3: Datenmigration (1 Tag)**
1. **Backup erstellen**
   ```bash
   cp buildwise.db buildwise_backup_$(date +%Y%m%d_%H%M%S).db
   ```

2. **Alembic Migration**
   ```bash
   # Neue Migration erstellen
   alembic revision --autogenerate -m "migrate_to_postgresql"
   
   # Migration ausführen
   alembic upgrade head
   ```

3. **Datenexport/Import (Alternative)**
   ```python
   # SQLite-Daten exportieren
   import sqlite3
   import json
   
   conn = sqlite3.connect('buildwise.db')
   cursor = conn.cursor()
   
   cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
   tables = cursor.fetchall()
   
   data = {}
   for table in tables:
       table_name = table[0]
       cursor.execute(f'SELECT * FROM {table_name}')
       rows = cursor.fetchall()
       data[table_name] = rows
   
   with open('sqlite_export.json', 'w') as f:
       json.dump(data, f, default=str)
   
   conn.close()
   ```

### **Phase 4: Tests & Optimierung (1 Tag)**
1. **Backend-Tests**
   ```bash
   # Server starten
   python -m uvicorn app.main:app --reload
   
   # API-Endpoints testen
   curl http://localhost:8000/api/v1/health
   ```

2. **Datenbank-Tests**
   ```sql
   -- Verbindung testen
   SELECT version();
   
   -- Tabellen prüfen
   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
   
   -- Daten prüfen
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM projects;
   ```

3. **Performance-Optimierung**
   ```sql
   -- Indizes erstellen
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_projects_owner_id ON projects(owner_id);
   CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
   
   -- JSONB-Indizes
   CREATE INDEX idx_users_social_profile_data ON users USING GIN(social_profile_data);
   CREATE INDEX idx_audit_logs_details ON audit_logs USING GIN(details);
   ```

## ⚠️ Risiken & Lösungen

### **1. Datentyp-Kompatibilität**
- **Risiko:** SQLite-Enums vs PostgreSQL-Enums
- **Lösung:** PostgreSQL-Enums definieren oder String-Felder verwenden

### **2. Transaktionsverhalten**
- **Risiko:** Unterschiedliche Isolation Levels
- **Lösung:** PostgreSQL-spezifische Transaktionskonfiguration

### **3. Performance**
- **Risiko:** Langsamere Abfragen bei großen Datenmengen
- **Lösung:** Indizes und Query-Optimierung

### **4. Backup & Recovery**
- **Risiko:** Datenverlust während Migration
- **Lösung:** Vollständiges Backup vor Migration

## 🔄 Rollback-Plan

Falls die Migration fehlschlägt:
1. **SQLite-Datenbank sichern**
   ```bash
   cp buildwise.db buildwise_backup_$(date +%Y%m%d_%H%M%S).db
   ```

2. **PostgreSQL-Datenbank löschen**
   ```sql
   DROP DATABASE buildwise;
   DROP USER buildwise_user;
   ```

3. **Zurück zu SQLite-Konfiguration**
   ```python
   # app/core/config.py
   database_url: str = "sqlite:///./buildwise.db"
   
   # app/core/database.py
   DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"
   ```

4. **Daten aus Backup wiederherstellen**
   ```bash
   cp buildwise_backup_*.db buildwise.db
   ```

## 📅 Timeline

| Phase | Dauer | Aufgaben |
|-------|-------|----------|
| **Vorbereitung** | 1-2 Tage | PostgreSQL installieren, Konfiguration anpassen, Tests erstellen |
| **Migration** | 1 Tag | Daten migrieren, Tests durchführen, Performance optimieren |
| **Deployment** | 1 Tag | Produktionsumgebung aktualisieren, Monitoring einrichten, Dokumentation aktualisieren |

**Gesamtdauer: 3-4 Tage**

## 🎯 Fazit

Die BuildWise-Datenbank ist gut strukturiert und die Migration zu PostgreSQL sollte relativ unkompliziert sein. Die wichtigsten Punkte:

1. **✅ Gute Kompatibilität:** Die meisten Datentypen sind direkt kompatibel
2. **✅ Strukturierte Daten:** Klare Beziehungen zwischen Tabellen
3. **✅ Audit-Trail:** Umfassendes Logging vorhanden
4. **✅ DSGVO-Compliance:** Datenschutz-Features implementiert

Die Migration bietet die Möglichkeit, von SQLite-spezifischen Einschränkungen zu profitieren und PostgreSQL-spezifische Features wie JSONB, native Enums und erweiterte Indizierung zu nutzen. 