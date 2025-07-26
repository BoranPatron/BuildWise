-- Fix milestones table - Add missing columns
-- Führe diese Befehle in der PostgreSQL-Datenbank aus

-- Prüfe ob Felder bereits existieren
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'milestones' 
AND column_name IN (
    'technical_specifications', 
    'quality_requirements', 
    'safety_requirements', 
    'environmental_requirements', 
    'category_specific_fields'
);

-- Füge fehlende Felder hinzu (nur wenn sie nicht existieren)
DO $$
BEGIN
    -- technical_specifications
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'milestones' AND column_name = 'technical_specifications'
    ) THEN
        ALTER TABLE milestones ADD COLUMN technical_specifications TEXT;
        RAISE NOTICE 'Added technical_specifications column';
    ELSE
        RAISE NOTICE 'technical_specifications column already exists';
    END IF;

    -- quality_requirements
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'milestones' AND column_name = 'quality_requirements'
    ) THEN
        ALTER TABLE milestones ADD COLUMN quality_requirements TEXT;
        RAISE NOTICE 'Added quality_requirements column';
    ELSE
        RAISE NOTICE 'quality_requirements column already exists';
    END IF;

    -- safety_requirements
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'milestones' AND column_name = 'safety_requirements'
    ) THEN
        ALTER TABLE milestones ADD COLUMN safety_requirements TEXT;
        RAISE NOTICE 'Added safety_requirements column';
    ELSE
        RAISE NOTICE 'safety_requirements column already exists';
    END IF;

    -- environmental_requirements
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'milestones' AND column_name = 'environmental_requirements'
    ) THEN
        ALTER TABLE milestones ADD COLUMN environmental_requirements TEXT;
        RAISE NOTICE 'Added environmental_requirements column';
    ELSE
        RAISE NOTICE 'environmental_requirements column already exists';
    END IF;

    -- category_specific_fields
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'milestones' AND column_name = 'category_specific_fields'
    ) THEN
        ALTER TABLE milestones ADD COLUMN category_specific_fields TEXT;
        RAISE NOTICE 'Added category_specific_fields column';
    ELSE
        RAISE NOTICE 'category_specific_fields column already exists';
    END IF;

END $$;

-- Zeige alle Felder in der milestones Tabelle
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'milestones' 
ORDER BY column_name; 