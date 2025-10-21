-- PostgreSQL Schema Check für deployed Version
-- Überprüft ob die hashed_password Spalte in der users Tabelle existiert

-- 1. Prüfe ob users Tabelle existiert
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_name = 'users' 
            AND table_schema = 'public'
        ) 
        THEN 'users Tabelle existiert' 
        ELSE 'users Tabelle existiert NICHT' 
    END as table_status;

-- 2. Prüfe ob hashed_password Spalte existiert
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'hashed_password'
            AND table_schema = 'public'
        ) 
        THEN 'hashed_password Spalte existiert' 
        ELSE 'hashed_password Spalte existiert NICHT' 
    END as column_status;

-- 3. Zeige alle Spalten der users Tabelle
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- 4. Zähle die Anzahl der Spalten
SELECT COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public';