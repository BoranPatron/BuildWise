#!/usr/bin/env python3
"""
Einfaches Debug-Skript für CostPositions
"""

import sqlite3
import os

def analyze_database():
    """Analysiert die Datenbank für CostPositions"""
    print("🔍 Starte einfache Datenbank-Analyse...")
    
    if not os.path.exists('buildwise.db'):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # 1. Prüfe alle Tabellen
        print("\n📊 Verfügbare Tabellen:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # 2. Prüfe Quotes-Tabelle
        print("\n📋 Quotes-Analyse:")
        cursor.execute("SELECT COUNT(*) FROM quotes")
        total_quotes = cursor.fetchone()[0]
        print(f"  Gesamte Quotes: {total_quotes}")
        
        cursor.execute("SELECT status, COUNT(*) FROM quotes GROUP BY status")
        quote_status = cursor.fetchall()
        for status, count in quote_status:
            print(f"  Status '{status}': {count}")
        
        # 3. Prüfe akzeptierte Quotes
        print("\n✅ Akzeptierte Quotes:")
        cursor.execute("""
            SELECT id, title, project_id, status, accepted_at 
            FROM quotes 
            WHERE status = 'accepted'
        """)
        accepted_quotes = cursor.fetchall()
        for quote in accepted_quotes:
            print(f"  Quote ID {quote[0]}: '{quote[1]}' (Projekt {quote[2]}) - Akzeptiert: {quote[4]}")
        
        # 4. Prüfe CostPositions-Tabelle
        print("\n💰 CostPositions-Analyse:")
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        total_cost_positions = cursor.fetchone()[0]
        print(f"  Gesamte CostPositions: {total_cost_positions}")
        
        if total_cost_positions > 0:
            cursor.execute("""
                SELECT id, title, project_id, quote_id, amount, status 
                FROM cost_positions
            """)
            cost_positions = cursor.fetchall()
            for cp in cost_positions:
                print(f"  CostPosition ID {cp[0]}: '{cp[1]}' (Projekt {cp[2]}, Quote {cp[3]}) - {cp[4]}€ - Status: {cp[5]}")
        
        # 5. Prüfe Projekte
        print("\n🏗️ Projekte:")
        cursor.execute("SELECT id, name FROM projects")
        projects = cursor.fetchall()
        for project in projects:
            print(f"  Projekt {project[0]}: {project[1]}")
        
        # 6. Prüfe Verbindung zwischen Quotes und CostPositions
        print("\n🔗 Quote-CostPosition-Verbindung:")
        cursor.execute("""
            SELECT q.id, q.title, q.status, cp.id, cp.title
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.status = 'accepted'
        """)
        connections = cursor.fetchall()
        for conn in connections:
            quote_id, quote_title, quote_status, cp_id, cp_title = conn
            if cp_id:
                print(f"  Quote {quote_id} ('{quote_title}') -> CostPosition {cp_id} ('{cp_title}')")
            else:
                print(f"  Quote {quote_id} ('{quote_title}') -> KEINE CostPosition")
        
        # 7. Prüfe spezifisch für Projekt 4 (falls vorhanden)
        print("\n🎯 Spezielle Analyse für Projekt 4:")
        cursor.execute("""
            SELECT q.id, q.title, q.status, cp.id, cp.title
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.project_id = 4 AND q.status = 'accepted'
        """)
        project4_connections = cursor.fetchall()
        if project4_connections:
            for conn in project4_connections:
                quote_id, quote_title, quote_status, cp_id, cp_title = conn
                if cp_id:
                    print(f"  Projekt 4 - Quote {quote_id} ('{quote_title}') -> CostPosition {cp_id} ('{cp_title}')")
                else:
                    print(f"  Projekt 4 - Quote {quote_id} ('{quote_title}') -> KEINE CostPosition")
        else:
            print("  Keine akzeptierten Quotes für Projekt 4 gefunden")
        
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Analyse: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def create_missing_cost_positions():
    """Erstellt fehlende CostPositions für akzeptierte Quotes"""
    print("\n🔧 Erstelle fehlende CostPositions...")
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Finde akzeptierte Quotes ohne CostPosition
        cursor.execute("""
            SELECT q.id, q.title, q.project_id, q.total_amount, q.currency, q.description,
                   q.company_name, q.contact_person, q.phone, q.email, q.website,
                   q.payment_terms, q.warranty_period, q.estimated_duration,
                   q.start_date, q.completion_date, q.labor_cost, q.material_cost,
                   q.overhead_cost, q.risk_score, q.price_deviation, q.ai_recommendation,
                   q.milestone_id
            FROM quotes q
            LEFT JOIN cost_positions cp ON q.id = cp.quote_id
            WHERE q.status = 'accepted' AND cp.id IS NULL
        """)
        quotes_without_cost_positions = cursor.fetchall()
        
        print(f"📋 Gefundene akzeptierte Quotes ohne CostPosition: {len(quotes_without_cost_positions)}")
        
        for quote in quotes_without_cost_positions:
            print(f"  Erstelle CostPosition für Quote {quote[0]} ('{quote[1]}')...")
            
            # Erstelle CostPosition
            cursor.execute("""
                INSERT INTO cost_positions (
                    project_id, title, description, amount, currency, category, cost_type, status,
                    contractor_name, contractor_contact, contractor_phone, contractor_email, contractor_website,
                    progress_percentage, paid_amount, payment_terms, warranty_period, estimated_duration,
                    start_date, completion_date, labor_cost, material_cost, overhead_cost,
                    risk_score, price_deviation, ai_recommendation, quote_id, milestone_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                quote[2],  # project_id
                f"Kostenposition: {quote[1]}",  # title
                quote[5] or f"Kostenposition basierend auf Angebot: {quote[1]}",  # description
                quote[3],  # amount
                quote[4] or "EUR",  # currency
                "other",  # category
                "quote_accepted",  # cost_type
                "active",  # status
                quote[6],  # contractor_name
                quote[7],  # contractor_contact
                quote[8],  # contractor_phone
                quote[9],  # contractor_email
                quote[10],  # contractor_website
                0.0,  # progress_percentage
                0.0,  # paid_amount
                quote[11],  # payment_terms
                quote[12],  # warranty_period
                quote[13],  # estimated_duration
                quote[14],  # start_date
                quote[15],  # completion_date
                quote[16],  # labor_cost
                quote[17],  # material_cost
                quote[18],  # overhead_cost
                quote[19],  # risk_score
                quote[20],  # price_deviation
                quote[21],  # ai_recommendation
                quote[0],  # quote_id
                quote[22]   # milestone_id
            ))
            
            print(f"    ✅ CostPosition erstellt für Quote {quote[0]}")
        
        conn.commit()
        print(f"✅ {len(quotes_without_cost_positions)} CostPositions erfolgreich erstellt")
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der CostPositions: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def main():
    """Hauptfunktion"""
    print("🚀 Starte einfache Debug-Analyse für CostPositions...")
    
    # 1. Datenbank-Analyse
    analyze_database()
    
    # 2. Erstelle fehlende CostPositions
    create_missing_cost_positions()
    
    # 3. Erneute Analyse
    print("\n🔄 Erneute Analyse nach Erstellung...")
    analyze_database()
    
    print("\n✅ Debug-Analyse abgeschlossen!")


if __name__ == "__main__":
    main() 