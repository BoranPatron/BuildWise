#!/usr/bin/env python3
"""
Verifizierung der tatsächlichen Daten in der Datenbank
"""

import sqlite3
import os

def verify_actual_data():
    """Überprüft die tatsächlichen Daten in der Datenbank"""
    print("🔍 Verifizierung der tatsächlichen Daten...")
    
    if not os.path.exists('buildwise.db'):
        print("❌ buildwise.db nicht gefunden!")
        return
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        print("\n📊 DATENBANK-STATUS:")
        print("=" * 50)
        
        # 1. Milestones (Gewerke)
        cursor.execute("SELECT COUNT(*) FROM milestones")
        milestones_count = cursor.fetchone()[0]
        print(f"📋 Milestones (Gewerke): {milestones_count}")
        
        if milestones_count > 0:
            cursor.execute("""
                SELECT id, title, description, status, project_id, created_at 
                FROM milestones 
                ORDER BY created_at DESC
            """)
            milestones = cursor.fetchall()
            
            print("\n📋 Milestones Details:")
            for m in milestones:
                print(f"  - ID {m[0]}: '{m[1]}' (Status: {m[3]}, Projekt: {m[4]})")
                print(f"    Beschreibung: {m[2]}")
                print(f"    Erstellt: {m[5]}")
                print()
        
        # 2. Quotes (Angebote)
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quotes_count = cursor.fetchone()[0]
        print(f"📋 Quotes (Angebote): {quotes_count}")
        
        if quotes_count > 0:
            cursor.execute("""
                SELECT id, title, milestone_id, status, total_amount, created_at 
                FROM quotes 
                ORDER BY created_at DESC
            """)
            quotes = cursor.fetchall()
            
            print("\n📋 Quotes Details:")
            for q in quotes:
                print(f"  - ID {q[0]}: '{q[1]}' (Milestone: {q[2]}, Status: {q[3]}, Betrag: {q[4]}€)")
                print(f"    Erstellt: {q[5]}")
                print()
        
        # 3. Cost Positions
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        cost_positions_count = cursor.fetchone()[0]
        print(f"📋 Cost Positions: {cost_positions_count}")
        
        if cost_positions_count > 0:
            cursor.execute("""
                SELECT id, title, amount, quote_id, milestone_id, created_at 
                FROM cost_positions 
                ORDER BY created_at DESC
            """)
            cost_positions = cursor.fetchall()
            
            print("\n📋 Cost Positions Details:")
            for cp in cost_positions:
                print(f"  - ID {cp[0]}: '{cp[1]}' (Betrag: {cp[2]}€, Quote: {cp[3]}, Milestone: {cp[4]})")
                print(f"    Erstellt: {cp[5]}")
                print()
        
        # 4. Projects
        cursor.execute("SELECT COUNT(*) FROM projects")
        projects_count = cursor.fetchone()[0]
        print(f"📋 Projects: {projects_count}")
        
        if projects_count > 0:
            cursor.execute("SELECT id, name, description FROM projects")
            projects = cursor.fetchall()
            
            print("\n📋 Projects Details:")
            for p in projects:
                print(f"  - ID {p[0]}: '{p[1]}'")
                print(f"    Beschreibung: {p[2]}")
                print()
        
        # 5. Verbindungen zwischen Milestones und Quotes
        print("\n🔗 VERBINDUNGEN:")
        print("=" * 30)
        
        cursor.execute("""
            SELECT m.id, m.title, COUNT(q.id) as quote_count
            FROM milestones m
            LEFT JOIN quotes q ON m.id = q.milestone_id
            GROUP BY m.id, m.title
            ORDER BY m.id
        """)
        connections = cursor.fetchall()
        
        print("Milestone → Quotes Verbindung:")
        for conn in connections:
            print(f"  - Milestone {conn[0]} ('{conn[1]}'): {conn[2]} Quotes")
        
        # 6. Verbindungen zwischen Quotes und Cost Positions
        cursor.execute("""
            SELECT q.id, q.title, COUNT(cp.id) as cost_position_count
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            GROUP BY q.id, q.title
            ORDER BY q.id
        """)
        quote_connections = cursor.fetchall()
        
        print("\nQuote → Cost Positions Verbindung:")
        for conn in quote_connections:
            print(f"  - Quote {conn[0]} ('{conn[1]}'): {conn[2]} Cost Positions")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎯 FAZIT:")
        print("=" * 20)
        
        if milestones_count > 0:
            print(f"✅ {milestones_count} Gewerke in der Datenbank vorhanden")
        else:
            print("❌ Keine Gewerke in der Datenbank")
            
        if quotes_count > 0:
            print(f"✅ {quotes_count} Angebote in der Datenbank vorhanden")
        else:
            print("❌ Keine Angebote in der Datenbank")
            
        if cost_positions_count > 0:
            print(f"✅ {cost_positions_count} Kostenpositionen in der Datenbank vorhanden")
        else:
            print("❌ Keine Kostenpositionen in der Datenbank")
        
    except Exception as e:
        print(f"❌ Fehler bei der Verifizierung: {e}")
        import traceback
        traceback.print_exc()
        conn.close()

if __name__ == "__main__":
    verify_actual_data() 