#!/usr/bin/env python3
"""
Führt das SQL-Skript aus, um fehlende CostPositions zu erstellen
"""

import sqlite3
import os

def execute_sql_fix():
    """Führt das SQL-Skript aus"""
    print("🔧 Führe CostPosition-Reparatur aus...")
    
    if not os.path.exists('buildwise.db'):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # 1. Prüfe akzeptierte Quotes ohne CostPosition
        print("\n📋 Prüfe akzeptierte Quotes ohne CostPosition...")
        cursor.execute("""
            SELECT q.id, q.title, q.project_id, q.total_amount 
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.status = 'accepted' AND cp.id IS NULL
        """)
        quotes_without_cost_positions = cursor.fetchall()
        
        print(f"Gefundene akzeptierte Quotes ohne CostPosition: {len(quotes_without_cost_positions)}")
        for quote in quotes_without_cost_positions:
            print(f"  Quote {quote[0]}: '{quote[1]}' (Projekt {quote[2]}) - {quote[3]}€")
        
        if len(quotes_without_cost_positions) == 0:
            print("✅ Alle akzeptierten Quotes haben bereits CostPositions")
            return
        
        # 2. Erstelle fehlende CostPositions
        print(f"\n🔧 Erstelle {len(quotes_without_cost_positions)} fehlende CostPositions...")
        
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
        print(f"✅ {len(quotes_without_cost_positions)} CostPositions erfolgreich erstellt")
        
        # 3. Zeige erstellte CostPositions
        print("\n💰 Erstellte CostPositions:")
        cursor.execute("""
            SELECT id, title, project_id, quote_id, amount, status 
            FROM cost_positions 
            WHERE quote_id IS NOT NULL
        """)
        cost_positions = cursor.fetchall()
        
        for cp in cost_positions:
            print(f"  CostPosition {cp[0]}: '{cp[1]}' (Projekt {cp[2]}, Quote {cp[3]}) - {cp[4]}€ - Status: {cp[5]}")
        
        # 4. Finale Validierung
        print("\n✅ Finale Validierung:")
        cursor.execute("""
            SELECT COUNT(*) FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.status = 'accepted' AND cp.id IS NULL
        """)
        remaining_missing = cursor.fetchone()[0]
        
        if remaining_missing == 0:
            print("✅ Alle akzeptierten Quotes haben jetzt CostPositions!")
        else:
            print(f"⚠️ {remaining_missing} Quotes haben immer noch keine CostPositions")
        
    except Exception as e:
        print(f"❌ Fehler bei der Reparatur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def main():
    """Hauptfunktion"""
    print("🚀 Starte CostPosition-Reparatur...")
    execute_sql_fix()
    print("\n✅ Reparatur abgeschlossen!")


if __name__ == "__main__":
    main() 