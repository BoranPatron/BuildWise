-- ============================================================================
-- Cleanup Script für automatisch erstellte DRAFT-Rechnungen
-- ============================================================================
-- 
-- Dieses Script entfernt alle automatisch generierten DRAFT-Rechnungen
-- mit AUTO-{id} Nummern, die beim Annehmen von Angeboten erstellt wurden.
--
-- WICHTIG: Dieses Script sollte nur auf Test/Dev-Umgebungen oder nach
-- sorgfältiger Prüfung auf Produktionsumgebungen ausgeführt werden!
--
-- ============================================================================

-- 1. Prüfe zuerst welche AUTO-Rechnungen existieren
SELECT 
    id,
    invoice_number,
    milestone_id,
    service_provider_id,
    total_amount,
    status,
    created_at
FROM invoices 
WHERE invoice_number LIKE 'AUTO-%'
ORDER BY id;

-- 2. Zähle die betroffenen Datensätze
SELECT 
    COUNT(*) as total_auto_invoices,
    COUNT(DISTINCT milestone_id) as affected_milestones,
    COUNT(DISTINCT service_provider_id) as affected_service_providers
FROM invoices 
WHERE invoice_number LIKE 'AUTO-%';

-- 3. Zeige zugehörige Kostenpositionen
SELECT 
    cp.id as cost_position_id,
    cp.invoice_id,
    i.invoice_number,
    cp.title,
    cp.amount
FROM cost_positions cp
JOIN invoices i ON cp.invoice_id = i.id
WHERE i.invoice_number LIKE 'AUTO-%';

-- ============================================================================
-- ACHTUNG: AB HIER WERDEN DATEN GELÖSCHT!
-- ============================================================================

-- 4. Beginne Transaktion (kann mit ROLLBACK rückgängig gemacht werden)
BEGIN TRANSACTION;

-- 5. Lösche zuerst die Kostenpositionen (Foreign Key Constraint)
DELETE FROM cost_positions 
WHERE invoice_id IN (
    SELECT id FROM invoices WHERE invoice_number LIKE 'AUTO-%'
);

-- Zeige Anzahl gelöschter Kostenpositionen
SELECT changes() as deleted_cost_positions;

-- 6. Lösche die AUTO-Rechnungen
DELETE FROM invoices 
WHERE invoice_number LIKE 'AUTO-%';

-- Zeige Anzahl gelöschter Rechnungen
SELECT changes() as deleted_invoices;

-- 7. Prüfe dass keine AUTO-Rechnungen mehr existieren
SELECT 
    COUNT(*) as remaining_auto_invoices
FROM invoices 
WHERE invoice_number LIKE 'AUTO-%';
-- Erwartung: 0

-- ============================================================================
-- ENTSCHEIDUNG: Änderungen übernehmen oder verwerfen
-- ============================================================================

-- Option A: Änderungen übernehmen
-- COMMIT;

-- Option B: Änderungen verwerfen (für Test-Durchläufe)
-- ROLLBACK;

-- ============================================================================
-- Alternative: Nur DRAFT-Rechnungen mit AUTO-Nummern löschen
-- ============================================================================
-- Falls Sie nur DRAFT-Status löschen möchten und andere behalten:

-- BEGIN TRANSACTION;
-- 
-- DELETE FROM cost_positions 
-- WHERE invoice_id IN (
--     SELECT id FROM invoices 
--     WHERE invoice_number LIKE 'AUTO-%' 
--     AND status = 'DRAFT'
-- );
-- 
-- DELETE FROM invoices 
-- WHERE invoice_number LIKE 'AUTO-%' 
-- AND status = 'DRAFT';
-- 
-- COMMIT;

-- ============================================================================
-- Verifikation nach dem Cleanup
-- ============================================================================

-- Prüfe dass alle AUTO-Rechnungen weg sind
SELECT * FROM invoices WHERE invoice_number LIKE 'AUTO-%';
-- Erwartung: Leeres Ergebnis

-- Prüfe dass keine verwaisten Kostenpositionen existieren
SELECT cp.* 
FROM cost_positions cp
LEFT JOIN invoices i ON cp.invoice_id = i.id
WHERE i.id IS NULL;
-- Erwartung: Leeres Ergebnis

-- Zeige Statistik der verbleibenden Rechnungen
SELECT 
    status,
    COUNT(*) as count,
    SUM(total_amount) as total_amount
FROM invoices
GROUP BY status;

-- ============================================================================
-- Ende des Cleanup Scripts
-- ============================================================================



