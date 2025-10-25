#!/bin/bash
# Dringendes Fix-Skript für Enum-Inkonsistenzen
# Dieses Skript muss direkt auf der Datenbank ausgeführt werden

echo "🚨 DRINGEND: Korrigiere Enum-Inkonsistenzen in der Datenbank..."

# Verwende psql direkt (ohne Python/SQLAlchemy)
psql $DATABASE_URL << 'EOF'
-- Korrigiere quotes.status Enum-Werte
UPDATE quotes SET status = 'accepted' WHERE status = 'ACCEPTED';
UPDATE quotes SET status = 'pending' WHERE status = 'PENDING';
UPDATE quotes SET status = 'rejected' WHERE status = 'REJECTED';
UPDATE quotes SET status = 'withdrawn' WHERE status = 'WITHDRAWN';
UPDATE quotes SET status = 'expired' WHERE status = 'EXPIRED';
UPDATE quotes SET status = 'submitted' WHERE status = 'SUBMITTED';
UPDATE quotes SET status = 'draft' WHERE status = 'DRAFT';

-- Zeige Anzahl der geänderten Zeilen
SELECT 'Quotes korrigiert:' as info, count(*) as anzahl FROM quotes WHERE status IN ('accepted', 'pending', 'rejected', 'withdrawn', 'expired', 'submitted', 'draft');

-- Korrigiere milestone_progress Enum-Werte (falls Tabelle existiert)
DO $$
BEGIN
    -- update_type Enum
    UPDATE milestone_progress SET update_type = 'comment' WHERE update_type = 'COMMENT';
    UPDATE milestone_progress SET update_type = 'completion' WHERE update_type = 'COMPLETION';
    UPDATE milestone_progress SET update_type = 'revision' WHERE update_type = 'REVISION';
    UPDATE milestone_progress SET update_type = 'defect' WHERE update_type = 'DEFECT';
    UPDATE milestone_progress SET update_type = 'status_change' WHERE update_type = 'STATUS_CHANGE';
    
    -- defect_severity Enum
    UPDATE milestone_progress SET defect_severity = 'minor' WHERE defect_severity = 'MINOR';
    UPDATE milestone_progress SET defect_severity = 'major' WHERE defect_severity = 'MAJOR';
    UPDATE milestone_progress SET defect_severity = 'critical' WHERE defect_severity = 'CRITICAL';
    
    RAISE NOTICE 'Milestone progress Enums korrigiert';
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'Tabelle milestone_progress existiert nicht';
END $$;

-- Korrigiere milestones completion_status
UPDATE milestones SET completion_status = 'in_progress' WHERE completion_status = 'IN_PROGRESS';
UPDATE milestones SET completion_status = 'completion_requested' WHERE completion_status = 'COMPLETION_REQUESTED';
UPDATE milestones SET completion_status = 'under_review' WHERE completion_status = 'UNDER_REVIEW';
UPDATE milestones SET completion_status = 'completed' WHERE completion_status = 'COMPLETED';
UPDATE milestones SET completion_status = 'completed_with_defects' WHERE completion_status = 'COMPLETED_WITH_DEFECTS';

-- Zeige Anzahl der geänderten Milestones
SELECT 'Milestones korrigiert:' as info, count(*) as anzahl FROM milestones WHERE completion_status IN ('in_progress', 'completion_requested', 'under_review', 'completed', 'completed_with_defects');

-- Finale Bestätigung
SELECT '✅ Enum-Korrektur abgeschlossen!' as status;
EOF

echo "✅ Enum-Korrektur erfolgreich abgeschlossen!"
