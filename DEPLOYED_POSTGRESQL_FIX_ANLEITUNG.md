# PostgreSQL Schema Fix für deployed Version

## Problem
Die deployed PostgreSQL-Datenbank hat ein älteres Schema ohne die `hashed_password` Spalte, was zu OAuth Microsoft Login-Fehlern führt.

## Sofortige Lösung

### 1. Schema überprüfen
Führen Sie in der deployed PostgreSQL-Datenbank aus:

```sql
-- Überprüfe das aktuelle Schema
\i deploy_schema_check.sql
```

Oder direkt in psql:
```bash
psql $DATABASE_URL -f deploy_schema_check.sql
```

### 2. Schema reparieren
Falls die `hashed_password` Spalte fehlt, führen Sie aus:

```sql
-- Füge die fehlende Spalte hinzu
\i deploy_schema_fix.sql
```

Oder direkt in psql:
```bash
psql $DATABASE_URL -f deploy_schema_fix.sql
```

### 3. Manuelle Lösung (falls SQL-Dateien nicht funktionieren)

```sql
-- Prüfe ob Spalte existiert
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name = 'hashed_password';

-- Falls keine Ergebnisse: Spalte hinzufügen
ALTER TABLE users ADD COLUMN hashed_password VARCHAR NULL;

-- Verifikation
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name = 'hashed_password';
```

## Langfristige Lösung

### Migration in deployed Version ausführen
```bash
# In der deployed Umgebung
alembic upgrade head
```

### Oder manuell alle fehlenden Spalten hinzufügen
```sql
-- Füge alle möglicherweise fehlenden Spalten hinzu
ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(9) NOT NULL DEFAULT 'EMAIL';
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS microsoft_sub VARCHAR NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS apple_sub VARCHAR NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS social_profile_data JSON NULL;
```

## Verifikation

Nach der Reparatur sollte der OAuth Microsoft Login funktionieren. Testen Sie:

1. Microsoft OAuth Login
2. Google OAuth Login (falls verwendet)
3. Normale E-Mail/Passwort Login

## Backup

**WICHTIG**: Erstellen Sie vor der Schema-Änderung ein Backup:

```bash
# PostgreSQL Backup
pg_dump $DATABASE_URL > backup_before_schema_fix.sql
```

## Fehlerbehebung

Falls Probleme auftreten:

1. **Permission denied**: Stellen Sie sicher, dass der Datenbankbenutzer ALTER-Berechtigung hat
2. **Connection timeout**: Überprüfen Sie die DATABASE_URL und Netzwerkverbindung
3. **SSL errors**: Fügen Sie `?sslmode=require` zur DATABASE_URL hinzu

## Monitoring

Überwachen Sie nach der Änderung:
- Anwendungslogs auf OAuth-Fehler
- Datenbankperformance
- Benutzer-Login-Erfolgsrate