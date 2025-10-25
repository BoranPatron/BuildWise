#!/bin/bash

# Direkte Datenbank-Korrektur für Enum-Inkonsistenzen
# Dieses Skript korrigiert die Quote-Status Enum-Werte direkt in der Datenbank

echo "🔧 Starting direct database enum fix..."

# PostgreSQL-Verbindung über psql
# Verwende die DATABASE_URL aus der Umgebung
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL environment variable not set"
    exit 1
fi

echo "📊 Current quote statuses before fix:"
psql "$DATABASE_URL" -c "SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL;"

echo ""
echo "🔧 Fixing quote statuses..."

# Korrigiere alle Enum-Werte
psql "$DATABASE_URL" -c "
UPDATE quotes SET status = 'accepted' WHERE status = 'ACCEPTED';
UPDATE quotes SET status = 'pending' WHERE status = 'PENDING';
UPDATE quotes SET status = 'rejected' WHERE status = 'REJECTED';
UPDATE quotes SET status = 'withdrawn' WHERE status = 'WITHDRAWN';
UPDATE quotes SET status = 'expired' WHERE status = 'EXPIRED';
"

echo "📊 Quote statuses after fix:"
psql "$DATABASE_URL" -c "SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL;"

echo ""
echo "🔧 Fixing milestone_progress enum values..."

# Korrigiere milestone_progress Enum-Werte falls Tabelle existiert
psql "$DATABASE_URL" -c "
UPDATE milestone_progress SET update_type = 'comment' WHERE update_type = 'COMMENT';
UPDATE milestone_progress SET update_type = 'completion' WHERE update_type = 'COMPLETION';
UPDATE milestone_progress SET update_type = 'revision' WHERE update_type = 'REVISION';
UPDATE milestone_progress SET update_type = 'defect' WHERE update_type = 'DEFECT';
UPDATE milestone_progress SET defect_severity = 'minor' WHERE defect_severity = 'MINOR';
UPDATE milestone_progress SET defect_severity = 'major' WHERE defect_severity = 'MAJOR';
UPDATE milestone_progress SET defect_severity = 'critical' WHERE defect_severity = 'CRITICAL';
" 2>/dev/null || echo "⚠️ milestone_progress table not found or already fixed"

echo ""
echo "✅ Database enum fix completed!"
echo "📊 Final quote statuses:"
psql "$DATABASE_URL" -c "SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL;"

echo ""
echo "🎉 All enum inconsistencies have been fixed!"
