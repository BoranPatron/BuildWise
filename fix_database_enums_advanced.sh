#!/bin/bash

# Erweiterte Datenbank-Analyse für Enum-Inkonsistenzen
echo "🔍 Deep analysis of enum inconsistencies..."

echo "📊 All quote records with their statuses:"
psql "$DATABASE_URL" -c "SELECT id, status, LENGTH(status) as status_length FROM quotes ORDER BY id;"

echo ""
echo "🔍 Looking for problematic enum values:"
psql "$DATABASE_URL" -c "SELECT status, COUNT(*) as count FROM quotes GROUP BY status ORDER BY status;"

echo ""
echo "🔍 Checking for hidden characters or encoding issues:"
psql "$DATABASE_URL" -c "SELECT status, ASCII(status) as ascii_code FROM quotes WHERE status != 'accepted';"

echo ""
echo "🔧 Attempting alternative fix approach..."

# Versuche eine andere Methode - erstelle temporäre Spalte
psql "$DATABASE_URL" -c "
-- Erstelle temporäre Spalte
ALTER TABLE quotes ADD COLUMN status_temp VARCHAR(20);

-- Kopiere alle Werte und konvertiere dabei
UPDATE quotes SET status_temp = CASE 
    WHEN status::text = 'ACCEPTED' THEN 'accepted'
    WHEN status::text = 'PENDING' THEN 'pending'
    WHEN status::text = 'REJECTED' THEN 'rejected'
    WHEN status::text = 'WITHDRAWN' THEN 'withdrawn'
    WHEN status::text = 'EXPIRED' THEN 'expired'
    ELSE status::text
END;

-- Zeige was kopiert wurde
SELECT status_temp, COUNT(*) as count FROM quotes GROUP BY status_temp ORDER BY status_temp;
"

echo ""
echo "🔧 Now updating the original column..."

# Jetzt aktualisiere die ursprüngliche Spalte
psql "$DATABASE_URL" -c "
UPDATE quotes SET status = status_temp::quotestatus WHERE status_temp IS NOT NULL;
"

echo ""
echo "🧹 Cleaning up temporary column..."
psql "$DATABASE_URL" -c "ALTER TABLE quotes DROP COLUMN status_temp;"

echo ""
echo "📊 Final verification:"
psql "$DATABASE_URL" -c "SELECT DISTINCT status FROM quotes WHERE status IS NOT NULL;"

echo ""
echo "✅ Alternative fix completed!"
