-- Erstellt fehlende CostPositions für akzeptierte Quotes
-- Führe dieses Skript in der SQLite-Datenbank aus

-- Prüfe akzeptierte Quotes ohne CostPosition
SELECT 'Akzeptierte Quotes ohne CostPosition:' as info;
SELECT q.id, q.title, q.project_id, q.total_amount 
FROM quotes q
LEFT JOIN cost_positions cp ON q.id = cp.quote_id
WHERE q.status = 'accepted' AND cp.id IS NULL;

-- Erstelle fehlende CostPositions
INSERT INTO cost_positions (
    project_id, title, description, amount, currency, category, cost_type, status,
    contractor_name, contractor_contact, contractor_phone, contractor_email, contractor_website,
    progress_percentage, paid_amount, payment_terms, warranty_period, estimated_duration,
    start_date, completion_date, labor_cost, material_cost, overhead_cost,
    risk_score, price_deviation, ai_recommendation, quote_id, milestone_id,
    created_at, updated_at
)
SELECT 
    q.project_id,
    'Kostenposition: ' || q.title,
    COALESCE(q.description, 'Kostenposition basierend auf Angebot: ' || q.title),
    q.total_amount,
    COALESCE(q.currency, 'EUR'),
    'other',
    'quote_accepted',
    'active',
    q.company_name,
    q.contact_person,
    q.phone,
    q.email,
    q.website,
    0.0,
    0.0,
    q.payment_terms,
    q.warranty_period,
    q.estimated_duration,
    q.start_date,
    q.completion_date,
    q.labor_cost,
    q.material_cost,
    q.overhead_cost,
    q.risk_score,
    q.price_deviation,
    q.ai_recommendation,
    q.id,
    q.milestone_id,
    datetime('now'),
    datetime('now')
FROM quotes q
LEFT JOIN cost_positions cp ON q.id = cp.quote_id
WHERE q.status = 'accepted' AND cp.id IS NULL;

-- Zeige erstellte CostPositions
SELECT 'Erstellte CostPositions:' as info;
SELECT id, title, project_id, quote_id, amount, status 
FROM cost_positions 
WHERE quote_id IS NOT NULL;

-- Zeige alle akzeptierten Quotes mit CostPositions
SELECT 'Alle akzeptierten Quotes mit CostPositions:' as info;
SELECT q.id, q.title, q.status, cp.id as cost_position_id, cp.title as cost_position_title
FROM quotes q
LEFT JOIN cost_positions cp ON q.id = cp.quote_id
WHERE q.status = 'accepted'; 