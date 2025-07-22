#!/usr/bin/env python3
"""
Überprüfung des Finance-Datenflusses
"""

import sqlite3
import os

def check_finance_data_flow():
    """Überprüft den Finance-Datenfluss"""
    print("🔍 Überprüfe Finance-Datenfluss...")
    
    if not os.path.exists('buildwise.db'):
        print("❌ buildwise.db nicht gefunden!")
        return
    
    print("✅ Datenbank buildwise.db gefunden")
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        print("\n📊 FINANCE-DATENFLUSS ANALYSE:")
        print("=" * 50)
        
        # 1. Milestones (Gewerke) - Quelle der Daten
        cursor.execute("SELECT COUNT(*) FROM milestones")
        milestones_count = cursor.fetchone()[0]
        print(f"📋 Milestones (Gewerke): {milestones_count}")
        
        if milestones_count > 0:
            print("   Details:")
            cursor.execute("SELECT id, title, status FROM milestones LIMIT 5")
            for row in cursor.fetchall():
                print(f"   - ID {row[0]}: {row[1]} ({row[2]})")
        
        # 2. Quotes (Angebote) - Zwischenschritt
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quotes_count = cursor.fetchone()[0]
        print(f"\n💰 Quotes (Angebote): {quotes_count}")
        
        if quotes_count > 0:
            print("   Details:")
            cursor.execute("SELECT id, milestone_id, status, total_amount FROM quotes LIMIT 5")
            for row in cursor.fetchall():
                print(f"   - ID {row[0]}: Milestone {row[1]}, Status: {row[2]}, Betrag: {row[3]}")
        
        # 3. Cost Positions - Was Finance anzeigt
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        cost_positions_count = cursor.fetchone()[0]
        print(f"\n💼 Cost Positions: {cost_positions_count}")
        
        if cost_positions_count > 0:
            print("   Details:")
            cursor.execute("SELECT id, title, amount, quote_id FROM cost_positions LIMIT 5")
            for row in cursor.fetchall():
                print(f"   - ID {row[0]}: {row[1]}, Betrag: {row[2]}, Quote ID: {row[3]}")
        
        # 4. Akzeptierte Quotes
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE status = 'accepted'")
        accepted_quotes_count = cursor.fetchone()[0]
        print(f"\n✅ Akzeptierte Quotes: {accepted_quotes_count}")
        
        # 5. Cost Positions aus akzeptierten Quotes
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions cp
            JOIN quotes q ON cp.quote_id = q.id
            WHERE q.status = 'accepted'
        """)
        accepted_cost_positions_count = cursor.fetchone()[0]
        print(f"💼 Cost Positions aus akzeptierten Quotes: {accepted_cost_positions_count}")
        
        print("\n🔍 PROBLEM-ANALYSE:")
        print("=" * 30)
        
        if milestones_count == 0:
            print("❌ Keine Milestones vorhanden → Keine Gewerke")
        elif quotes_count == 0:
            print("❌ Keine Quotes vorhanden → Keine Angebote für Gewerke")
        elif accepted_quotes_count == 0:
            print("❌ Keine akzeptierten Quotes → Keine akzeptierten Angebote")
        elif accepted_cost_positions_count == 0:
            print("❌ Keine Cost Positions aus akzeptierten Quotes → Finance zeigt nichts an")
        else:
            print("✅ Alle Daten vorhanden → Finance sollte funktionieren")
        
        print("\n💡 LÖSUNG:")
        print("=" * 15)
        print("1. Gewerke erstellen (Milestones)")
        print("2. Angebote erstellen (Quotes)")
        print("3. Angebote akzeptieren (Quotes → accepted)")
        print("4. Cost Positions werden automatisch erstellt")
        print("5. Finance zeigt Cost Positions an")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_finance_data_flow() 