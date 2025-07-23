# PostgreSQL Migration - Zusammenfassung

## 📊 Aktuelle Situation

**BuildWise verwendet aktuell:**
- **Datenbank**: SQLite 3.x (`buildwise.db`)
- **Tabellen**: 13 Tabellen
- **Datensätze**: ~450 Zeilen
- **Haupttabellen**: users (7), projects (11), audit_logs (407), milestones (11), quotes (3), cost_positions (2), buildwise_fees (2), documents (7), expenses (0)

## 🎯 Migrationsziele

### **Vorteile von PostgreSQL:**
1. **Skalierbarkeit**: Bessere Performance bei großen Datenmengen
2. **Erweiterte Features**: JSONB, native Enums, erweiterte Indizierung
3. **Sicherheit**: Row Level Security (RLS), bessere Verschlüsselung
4. **Konkurrenz**: Bessere Unterstützung für gleichzeitige Zugriffe
5. **Backup & Recovery**: Robuste Backup-Strategien

## 📋 Migrationsplan

### **Phase 1: Vorbereitung (1-2 Tage)**
```bash
# PostgreSQL installieren
sudo apt install postgresql postgresql-contrib  # Ubuntu/Debian
# oder: https://www.postgresql.org/download/windows/  # Windows
# oder: brew install postgresql  # macOS

# Datenbank erstellen
CREATE DATABASE buildwise;
CREATE USER buildwise_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE buildwise TO buildwise_user;
```

### **Phase 2: Konfiguration (1 Tag)**
```python
# app/core/config.py
database_url: str = "postgresql+asyncpg://buildwise_user:your_secure_password@localhost:5432/buildwise"

# app/core/database.py
DATABASE_URL = "postgresql+asyncpg://buildwise_user:your_secure_password@localhost:5432/buildwise"

# requirements.txt
asyncpg>=0.28.0
psycopg2-binary>=2.9.0
# aiosqlite entfernen
```

### **Phase 3: Datenmigration (1 Tag)**
```bash
# Backup erstellen
cp buildwise.db buildwise_backup_$(date +%Y%m%d_%H%M%S).db

# Alembic Migration
alembic revision --autogenerate -m "migrate_to_postgresql"
alembic upgrade head
```

### **Phase 4: Tests & Optimierung (1 Tag)**
```sql
-- Performance-Optimierungen
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

-- JSONB-Indizes
CREATE INDEX idx_users_social_profile_data ON users USING GIN(social_profile_data);
CREATE INDEX idx_audit_logs_details ON audit_logs USING GIN(details);
```

## ⚠️ Wichtige Punkte

### **Datentyp-Kompatibilität:**
- ✅ **INTEGER, TEXT, VARCHAR, BOOLEAN**: Direkt kompatibel
- ✅ **FLOAT**: → `DOUBLE PRECISION`
- ✅ **DATETIME**: → `TIMESTAMP WITH TIME ZONE`
- ✅ **JSON**: → `JSONB` (besser für PostgreSQL)

### **Besondere Herausforderungen:**
1. **Enums**: SQLite VARCHAR → PostgreSQL native ENUMs
2. **Zeitzonen**: Explizite Zeitzonen-Handhabung erforderlich
3. **JSON-Felder**: JSONB für bessere Performance

### **Sicherheitsaspekte:**
```sql
-- Row Level Security (RLS)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY project_owner_policy ON projects
    FOR ALL USING (owner_id = current_user_id());
```

## 🔄 Rollback-Plan

Falls Migration fehlschlägt:
1. SQLite-Datenbank sichern
2. PostgreSQL-Datenbank löschen
3. Zurück zu SQLite-Konfiguration
4. Daten aus Backup wiederherstellen

## 📅 Timeline

| Phase | Dauer | Status |
|-------|-------|--------|
| **Vorbereitung** | 1-2 Tage | PostgreSQL installieren, Konfiguration anpassen |
| **Migration** | 1 Tag | Daten migrieren, Tests durchführen |
| **Deployment** | 1 Tag | Produktionsumgebung aktualisieren |

**Gesamtdauer: 3-4 Tage**

## 🎯 Fazit

Die Migration von SQLite zu PostgreSQL ist **gut machbar** und bietet erhebliche Vorteile:

✅ **Gute Kompatibilität** der meisten Datentypen  
✅ **Strukturierte Daten** mit klaren Beziehungen  
✅ **Umfassender Audit-Trail** vorhanden  
✅ **DSGVO-Compliance** implementiert  

Die Migration ermöglicht es BuildWise, von PostgreSQL-spezifischen Features zu profitieren und die Skalierbarkeit für zukünftiges Wachstum sicherzustellen.

---

**📋 Nächste Schritte:**
1. PostgreSQL installieren
2. Konfigurationsdateien anpassen
3. Dependencies aktualisieren
4. Migration durchführen
5. Tests durchführen
6. Performance optimieren 