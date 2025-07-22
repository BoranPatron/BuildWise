# 🔧 Datenbank-Reparatur Anleitung

## 📍 Aktuelle Situation

Die Daten werden in der **SQLite-Datenbank `buildwise.db`** abgelegt, die sich im Hauptverzeichnis des BuildWise-Projekts befindet.

### 🔍 Problem-Analyse

- **Datenbank-Typ**: SQLite (nicht PostgreSQL)
- **Datenbank-Datei**: `buildwise.db` (112KB)
- **Problem**: Die Tabellen `cost_positions` und `quotes` sind leer oder haben keine Daten
- **Folge**: Im Finance-Dashboard werden keine Kostenpositionen angezeigt

## 🛠️ Lösung

### Schritt 1: Datenbank-Überprüfung

Führen Sie das Reparatur-Skript aus:

```bash
python check_and_fix_database.py
```

### Schritt 2: Alternative - Manuelle Überprüfung

Falls das Python-Skript nicht funktioniert, können Sie die Datenbank direkt überprüfen:

```bash
# SQLite-Datenbank öffnen
sqlite3 buildwise.db

# Tabellen auflisten
.tables

# Daten in wichtigen Tabellen überprüfen
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM quotes;
SELECT COUNT(*) FROM cost_positions;

# Akzeptierte Quotes anzeigen
SELECT id, title, status FROM quotes WHERE status = 'accepted';

# CostPositions für akzeptierte Quotes
SELECT cp.id, cp.title, q.title as quote_title 
FROM cost_positions cp 
JOIN quotes q ON cp.quote_id = q.id 
WHERE q.status = 'accepted';

# Beenden
.quit
```

### Schritt 3: Manuelle Reparatur

Falls das automatische Skript nicht funktioniert, können Sie die Reparatur manuell durchführen:

```sql
-- 1. Test-Daten erstellen (falls nötig)
INSERT INTO users (email, hashed_password, first_name, last_name, user_type, is_active, is_verified, created_at, updated_at)
VALUES ('admin@buildwise.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8qQqKqG', 'Admin', 'User', 'admin', 1, 1, datetime('now'), datetime('now'));

-- 2. Projekt erstellen
INSERT INTO projects (name, description, project_type, status, budget, address_street, address_zip, address_city, owner_id, created_at, updated_at)
VALUES ('Test-Projekt', 'Ein Test-Projekt', 'renovation', 'active', 50000.0, 'Teststraße 1', '12345', 'Teststadt', 1, datetime('now'), datetime('now'));

-- 3. Akzeptierte Quote erstellen
INSERT INTO quotes (title, description, total_amount, currency, status, company_name, contact_person, phone, email, project_id, service_provider_id, accepted_at, created_at, updated_at)
VALUES ('Test-Angebot', 'Ein Test-Angebot', 15000.0, 'EUR', 'accepted', 'Bauunternehmen', 'Max Mustermann', '+49 123 456789', 'max@example.com', 1, 1, datetime('now'), datetime('now'), datetime('now'));

-- 4. CostPosition für akzeptierte Quote erstellen
INSERT INTO cost_positions (project_id, title, description, amount, currency, category, cost_type, status, contractor_name, contractor_contact, contractor_phone, contractor_email, progress_percentage, paid_amount, quote_id, created_at, updated_at)
VALUES (1, 'Kostenposition: Test-Angebot', 'Kostenposition basierend auf Angebot: Test-Angebot', 15000.0, 'EUR', 'other', 'quote_accepted', 'active', 'Bauunternehmen', 'Max Mustermann', '+49 123 456789', 'max@example.com', 0.0, 0.0, 1, datetime('now'), datetime('now'));
```

## 🔍 Überprüfung

Nach der Reparatur sollten Sie folgende Ergebnisse sehen:

1. **Benutzer**: Mindestens 1 Admin-Benutzer
2. **Projekte**: Mindestens 1 Test-Projekt
3. **Quotes**: Mindestens 1 akzeptierte Quote
4. **CostPositions**: Mindestens 1 CostPosition für die akzeptierte Quote

## 💡 Finance-Dashboard Test

Nach der Reparatur:

1. Starten Sie den Backend-Server
2. Öffnen Sie das Frontend
3. Navigieren Sie zum Finance-Dashboard
4. Sie sollten jetzt Kostenpositionen sehen

## 🚨 Wichtige Hinweise

- **Backup**: Erstellen Sie vor der Reparatur ein Backup der `buildwise.db` Datei
- **Test-Umgebung**: Testen Sie die Reparatur zuerst in einer Test-Umgebung
- **Datenverlust**: Die Reparatur kann bestehende Daten überschreiben

## 📞 Support

Falls die Reparatur nicht funktioniert:

1. Überprüfen Sie die Python-Installation
2. Stellen Sie sicher, dass SQLite installiert ist
3. Überprüfen Sie die Dateiberechtigungen für `buildwise.db`
4. Kontaktieren Sie den Support mit den Fehlermeldungen 