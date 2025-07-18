-- SQL-Skript zur Behebung der fehlenden Geocoding-Daten
-- Führen Sie dieses Skript in Ihrer PostgreSQL-Datenbank aus

-- 1. Füge Adressen zu bestehenden Projekten hinzu
UPDATE projects 
SET address = 'Hauptstraße 42, 80331 München, Deutschland'
WHERE id = 1 AND (address IS NULL OR address = '');

UPDATE projects 
SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland'
WHERE id = 2 AND (address IS NULL OR address = '');

UPDATE projects 
SET address = 'Neuer Wall 80, 20354 Hamburg, Deutschland'
WHERE id = 3 AND (address IS NULL OR address = '');

UPDATE projects 
SET address = 'Zeil 106, 60313 Frankfurt am Main, Deutschland'
WHERE id = 4 AND (address IS NULL OR address = '');

UPDATE projects 
SET address = 'Friedrichstraße 123, 10117 Berlin, Deutschland'
WHERE id = 5 AND (address IS NULL OR address = '');

-- 2. Stelle sicher, dass Projekte öffentlich sind und Quotes erlaubt sind
UPDATE projects 
SET is_public = true, allow_quotes = true
WHERE id IN (1, 2, 3, 4, 5);

-- 3. Zeige die aktualisierten Projekte an
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

-- 4. Zeige alle Milestones/Gewerke an
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

-- 5. Zeige Statistiken
SELECT 
    'Projekte gesamt' as statistik,
    COUNT(*) as anzahl
FROM projects
UNION ALL
SELECT 
    'Projekte mit Adressen',
    COUNT(*)
FROM projects
WHERE address IS NOT NULL AND address != ''
UNION ALL
SELECT 
    'Projekte öffentlich',
    COUNT(*)
FROM projects
WHERE is_public = true
UNION ALL
SELECT 
    'Gewerke gesamt',
    COUNT(*)
FROM milestones
UNION ALL
SELECT 
    'Gewerke mit öffentlichen Projekten',
    COUNT(*)
FROM milestones m
JOIN projects p ON m.project_id = p.id
WHERE p.is_public = true AND p.allow_quotes = true; 