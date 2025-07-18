# Manuelle Datenbank-Behebung für Geo-Karten-Problem

## Problem
Die Gewerke werden in der Dienstleisteransicht unter "Karte" nicht angezeigt, weil die Projekte keine Adressen und damit keine Geokoordinaten haben.

## Lösung

### 1. Datenbank-Verbindung herstellen

**Option A: pgAdmin**
1. Öffnen Sie pgAdmin
2. Verbinden Sie sich mit dem PostgreSQL-Server
3. Wählen Sie die Datenbank `buildwise`

**Option B: DBeaver**
1. Öffnen Sie DBeaver
2. Erstellen Sie eine neue Verbindung zu PostgreSQL
3. Verbindungsdaten:
   - Host: localhost
   - Port: 5432
   - Database: buildwise
   - Username: postgres
   - Password: your_secure_password

**Option C: Kommandozeile**
```bash
psql -h localhost -U postgres -d buildwise
```

### 2. Aktuelle Projekte anzeigen

Führen Sie diese SQL-Abfrage aus:

```sql
SELECT 
    id,
    name,
    address,
    is_public,
    allow_quotes,
    address_latitude,
    address_longitude
FROM projects 
ORDER BY id;
```

### 3. Adressen zu Projekten hinzufügen

Führen Sie diese SQL-Befehle aus:

```sql
-- Projekt 1
UPDATE projects 
SET address = 'Hauptstraße 42, 80331 München, Deutschland'
WHERE id = 1 AND (address IS NULL OR address = '');

-- Projekt 2
UPDATE projects 
SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland'
WHERE id = 2 AND (address IS NULL OR address = '');

-- Projekt 3
UPDATE projects 
SET address = 'Neuer Wall 80, 20354 Hamburg, Deutschland'
WHERE id = 3 AND (address IS NULL OR address = '');

-- Projekt 4
UPDATE projects 
SET address = 'Zeil 106, 60313 Frankfurt am Main, Deutschland'
WHERE id = 4 AND (address IS NULL OR address = '');

-- Projekt 5
UPDATE projects 
SET address = 'Friedrichstraße 123, 10117 Berlin, Deutschland'
WHERE id = 5 AND (address IS NULL OR address = '');
```

### 4. Projekte öffentlich machen

```sql
UPDATE projects 
SET is_public = true, allow_quotes = true 
WHERE id IN (1, 2, 3, 4, 5);
```

### 5. Überprüfung

Führen Sie diese Abfrage aus, um zu überprüfen, ob die Änderungen erfolgreich waren:

```sql
SELECT 
    id,
    name,
    address,
    is_public,
    allow_quotes,
    address_latitude,
    address_longitude
FROM projects 
WHERE id IN (1, 2, 3, 4, 5)
ORDER BY id;
```

### 6. Gewerke anzeigen

```sql
SELECT 
    m.id,
    m.title,
    m.category,
    m.status,
    p.name as project_name,
    p.address as project_address,
    p.is_public,
    p.allow_quotes
FROM milestones m
JOIN projects p ON m.project_id = p.id
ORDER BY m.id;
```

## Backend neu starten

Nach den Datenbank-Änderungen müssen Sie das Backend neu starten:

```bash
# Stoppen Sie das laufende Backend (Ctrl+C)
# Dann starten Sie es neu:
python -m uvicorn app.main:app --reload
```

## Testen

1. Warten Sie 10-15 Sekunden bis das Backend vollständig gestartet ist
2. Öffnen Sie die Dienstleisteransicht in der BuildWise-Anwendung
3. Gehen Sie zu "Karte"
4. Die Gewerke sollten jetzt als Marker auf der Karte angezeigt werden

## Debugging

Falls die Gewerke immer noch nicht angezeigt werden:

1. Öffnen Sie die Browser-Entwicklertools (F12)
2. Gehen Sie zur Konsole
3. Führen Sie das Debug-Skript aus:
   ```javascript
   // Kopieren Sie den Inhalt von debug_geo_search_final.js
   // und führen Sie ihn in der Konsole aus
   ```

## Automatisches Geocoding

Das Backend führt automatisch Geocoding für Projekte mit Adressen durch. Nach dem Neustart des Backends sollten die `address_latitude` und `address_longitude` Felder automatisch gefüllt werden.

## Troubleshooting

**Problem: "password authentication failed"**
- Überprüfen Sie die Datenbank-Credentials in der `.env`-Datei
- Stellen Sie sicher, dass PostgreSQL läuft

**Problem: "connection refused"**
- Stellen Sie sicher, dass PostgreSQL auf localhost:5432 läuft
- Überprüfen Sie die Firewall-Einstellungen

**Problem: Gewerke werden immer noch nicht angezeigt**
- Überprüfen Sie, ob die Projekte `is_public = true` haben
- Überprüfen Sie, ob die Projekte `allow_quotes = true` haben
- Überprüfen Sie, ob die Adressen korrekt gesetzt sind
- Überprüfen Sie die Browser-Konsole auf JavaScript-Fehler 