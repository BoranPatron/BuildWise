import sqlite3

print("🔧 Quick Fix für CostPositions...")

try:
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Prüfe akzeptierte Quotes
    cursor.execute("SELECT COUNT(*) FROM quotes WHERE status = 'accepted'")
    accepted_count = cursor.fetchone()[0]
    print(f"Akzeptierte Quotes: {accepted_count}")
    
    # Prüfe CostPositions
    cursor.execute("SELECT COUNT(*) FROM cost_positions")
    cost_positions_count = cursor.fetchone()[0]
    print(f"CostPositions: {cost_positions_count}")
    
    # Erstelle fehlende CostPositions
    cursor.execute("""
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
        WHERE q.status = 'accepted' AND cp.id IS NULL
    """)
    
    conn.commit()
    print("✅ CostPositions erstellt")
    
    # Zeige Ergebnis
    cursor.execute("SELECT COUNT(*) FROM cost_positions")
    new_count = cursor.fetchone()[0]
    print(f"Neue CostPositions: {new_count}")
    
    conn.close()
    print("✅ Fix abgeschlossen")
    
except Exception as e:
    print(f"❌ Fehler: {e}") 