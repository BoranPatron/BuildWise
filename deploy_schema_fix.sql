-- PostgreSQL Schema Fix für deployed Version
-- Fügt die fehlende hashed_password Spalte zur users Tabelle hinzu

-- 1. Überprüfe ob die Spalte bereits existiert
DO $$
BEGIN
    -- Prüfe ob hashed_password Spalte existiert
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'hashed_password'
        AND table_schema = 'public'
    ) THEN
        -- Füge die fehlende Spalte hinzu
        ALTER TABLE users ADD COLUMN hashed_password VARCHAR NULL;
        
        -- Log die Änderung
        RAISE NOTICE 'hashed_password Spalte erfolgreich zur users Tabelle hinzugefügt';
    ELSE
        -- Spalte existiert bereits
        RAISE NOTICE 'hashed_password Spalte existiert bereits in der users Tabelle';
    END IF;
END $$;

-- 2. Verifiziere die Änderung
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name = 'hashed_password'
AND table_schema = 'public';

-- 3. Zeige alle Spalten der users Tabelle zur Verifikation
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public'
ORDER BY ordinal_position;