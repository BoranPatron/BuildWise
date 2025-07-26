-- Füge technische Felder zur milestones Tabelle hinzu
-- Führe dieses Script in der PostgreSQL-Datenbank aus

-- Prüfe ob Felder bereits existieren und füge sie hinzu
DO $$
BEGIN
    -- Technische Spezifikationen
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'technical_specifications') THEN
        ALTER TABLE milestones ADD COLUMN technical_specifications TEXT;
        RAISE NOTICE 'Feld technical_specifications hinzugefügt';
    ELSE
        RAISE NOTICE 'Feld technical_specifications existiert bereits';
    END IF;

    -- Qualitätsanforderungen
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'quality_requirements') THEN
        ALTER TABLE milestones ADD COLUMN quality_requirements TEXT;
        RAISE NOTICE 'Feld quality_requirements hinzugefügt';
    ELSE
        RAISE NOTICE 'Feld quality_requirements existiert bereits';
    END IF;

    -- Sicherheitsanforderungen
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'safety_requirements') THEN
        ALTER TABLE milestones ADD COLUMN safety_requirements TEXT;
        RAISE NOTICE 'Feld safety_requirements hinzugefügt';
    ELSE
        RAISE NOTICE 'Feld safety_requirements existiert bereits';
    END IF;

    -- Umweltanforderungen
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'environmental_requirements') THEN
        ALTER TABLE milestones ADD COLUMN environmental_requirements TEXT;
        RAISE NOTICE 'Feld environmental_requirements hinzugefügt';
    ELSE
        RAISE NOTICE 'Feld environmental_requirements existiert bereits';
    END IF;

    -- Kategorie-spezifische Felder
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'category_specific_fields') THEN
        ALTER TABLE milestones ADD COLUMN category_specific_fields TEXT;
        RAISE NOTICE 'Feld category_specific_fields hinzugefügt';
    ELSE
        RAISE NOTICE 'Feld category_specific_fields existiert bereits';
    END IF;

END $$;

-- Zeige die aktuelle Tabellenstruktur
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'milestones' 
ORDER BY ordinal_position; 