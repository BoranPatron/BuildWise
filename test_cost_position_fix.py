#!/usr/bin/env python3
"""
Test-Skript für CostPosition-Reparatur
"""

import sqlite3
import os

def test_cost_position_fix():
    """Testet die CostPosition-Reparatur"""
    print("🧪 Teste CostPosition-Reparatur...")
    
    if not os.path.exists('buildwise.db'):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # 1. Prüfe akzeptierte Quotes
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE status = 'accepted'")
        accepted_quotes = cursor.fetchone()[0]
        print(f"📋 Akzeptierte Quotes: {accepted_quotes}")
        
        # 2. Prüfe CostPositions
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        total_cost_positions = cursor.fetchone()[0]
        print(f"💰 Gesamte CostPositions: {total_cost_positions}")
        
        # 3. Prüfe CostPositions mit Quote-Referenz
        cursor.execute("SELECT COUNT(*) FROM cost_positions WHERE quote_id IS NOT NULL")
        cost_positions_with_quotes = cursor.fetchone()[0]
        print(f"🔗 CostPositions mit Quote-Referenz: {cost_positions_with_quotes}")
        
        # 4. Prüfe fehlende CostPositions
        cursor.execute("""
            SELECT COUNT(*) FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.status = 'accepted' AND cp.id IS NULL
        """)
        missing_cost_positions = cursor.fetchone()[0]
        print(f"❌ Fehlende CostPositions: {missing_cost_positions}")
        
        # 5. Zeige Details der akzeptierten Quotes
        print("\n📋 Details der akzeptierten Quotes:")
        cursor.execute("""
            SELECT q.id, q.title, q.project_id, q.total_amount, cp.id as cost_position_id
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.status = 'accepted'
        """)
        accepted_quotes_details = cursor.fetchall()
        
        for quote in accepted_quotes_details:
            quote_id, title, project_id, amount, cost_position_id = quote
            if cost_position_id:
                print(f"  ✅ Quote {quote_id}: '{title}' (Projekt {project_id}) - {amount}€ -> CostPosition {cost_position_id}")
            else:
                print(f"  ❌ Quote {quote_id}: '{title}' (Projekt {project_id}) - {amount}€ -> KEINE CostPosition")
        
        # 6. Zeige alle CostPositions
        print("\n💰 Alle CostPositions:")
        cursor.execute("""
            SELECT id, title, project_id, quote_id, amount, status
            FROM cost_positions
            ORDER BY id
        """)
        cost_positions = cursor.fetchall()
        
        for cp in cost_positions:
            cp_id, title, project_id, quote_id, amount, status = cp
            print(f"  CostPosition {cp_id}: '{title}' (Projekt {project_id}, Quote {quote_id}) - {amount}€ - Status: {status}")
        
        # 7. Zusammenfassung
        print(f"\n📊 Zusammenfassung:")
        print(f"  • Akzeptierte Quotes: {accepted_quotes}")
        print(f"  • Gesamte CostPositions: {total_cost_positions}")
        print(f"  • CostPositions mit Quote-Referenz: {cost_positions_with_quotes}")
        print(f"  • Fehlende CostPositions: {missing_cost_positions}")
        
        if missing_cost_positions == 0:
            print("✅ Alle akzeptierten Quotes haben CostPositions!")
        else:
            print(f"⚠️ {missing_cost_positions} akzeptierte Quotes haben keine CostPositions")
        
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def fix_missing_cost_positions():
    """Repariert fehlende CostPositions"""
    print("\n🔧 Repariere fehlende CostPositions...")
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
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
        print("✅ Fehlende CostPositions erstellt")
        
    except Exception as e:
        print(f"❌ Fehler bei der Reparatur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def main():
    """Hauptfunktion"""
    print("🚀 Starte CostPosition-Test und Reparatur...")
    
    # 1. Teste aktuellen Zustand
    test_cost_position_fix()
    
    # 2. Repariere fehlende CostPositions
    fix_missing_cost_positions()
    
    # 3. Teste erneut
    print("\n🔄 Teste nach Reparatur...")
    test_cost_position_fix()
    
    print("\n✅ Test und Reparatur abgeschlossen!")


if __name__ == "__main__":
    main() 