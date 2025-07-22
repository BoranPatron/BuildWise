#!/usr/bin/env python3
"""
Überprüfung und Reparatur der BuildWise-Datenbank
"""

import sqlite3
import os
from datetime import datetime

def check_database_status():
    """Überprüft den aktuellen Status der Datenbank"""
    print("🔍 Überprüfe Datenbank-Status...")
    
    if not os.path.exists('buildwise.db'):
        print("❌ Datenbank buildwise.db nicht gefunden!")
        return False
    
    print("✅ Datenbank buildwise.db gefunden")
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Alle Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Verfügbare Tabellen ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Wichtige Tabellen überprüfen
        important_tables = {
            'users': 'Benutzer',
            'projects': 'Projekte', 
            'quotes': 'Angebote',
            'cost_positions': 'Kostenpositionen',
            'milestones': 'Meilensteine'
        }
        
        print(f"\n📊 Daten-Übersicht:")
        for table, description in important_tables.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {description} ({table}): {count} Einträge")
                
                if count > 0:
                    # Erste Einträge anzeigen
                    cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                    rows = cursor.fetchall()
                    for i, row in enumerate(rows):
                        print(f"    {i+1}. {row}")
            except Exception as e:
                print(f"  - {description} ({table}): Fehler - {e}")
        
        # Spezielle Analyse für Quotes und CostPositions
        print(f"\n🎯 Spezielle Analyse:")
        
        # Akzeptierte Quotes
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE status = 'accepted'")
        accepted_quotes = cursor.fetchone()[0]
        print(f"  - Akzeptierte Quotes: {accepted_quotes}")
        
        # CostPositions für akzeptierte Quotes
        cursor.execute("""
            SELECT COUNT(*) FROM cost_positions cp
            JOIN quotes q ON cp.quote_id = q.id
            WHERE q.status = 'accepted'
        """)
        cost_positions_for_accepted = cursor.fetchone()[0]
        print(f"  - CostPositions für akzeptierte Quotes: {cost_positions_for_accepted}")
        
        # Fehlende CostPositions
        missing_cost_positions = accepted_quotes - cost_positions_for_accepted
        print(f"  - Fehlende CostPositions: {missing_cost_positions}")
        
        if missing_cost_positions > 0:
            print(f"  ⚠️  {missing_cost_positions} akzeptierte Quotes haben keine CostPositions!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Überprüfung: {e}")
        conn.close()
        return False

def create_test_data():
    """Erstellt Test-Daten falls die Datenbank leer ist"""
    print("\n🔧 Erstelle Test-Daten...")
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Prüfe ob bereits Daten vorhanden sind
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("📝 Erstelle Test-Benutzer...")
            
            # Admin-Benutzer erstellen
            cursor.execute("""
                INSERT INTO users (
                    email, hashed_password, first_name, last_name, user_type, 
                    is_active, is_verified, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                'admin@buildwise.com',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8qQqKqG',  # admin123
                'Admin',
                'User',
                'admin',
                True,
                True
            ))
            
            # Service Provider erstellen
            cursor.execute("""
                INSERT INTO users (
                    email, hashed_password, first_name, last_name, user_type,
                    company_name, address_street, address_zip, address_city,
                    is_active, is_verified, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                'dienstleister@example.com',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8qQqKqG',  # admin123
                'Max',
                'Mustermann',
                'service_provider',
                'Bauunternehmen Mustermann',
                'Musterstraße 1',
                '12345',
                'Musterstadt',
                True,
                True
            ))
            
            print("✅ Test-Benutzer erstellt")
        
        # Prüfe Projekte
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        
        if project_count == 0:
            print("📝 Erstelle Test-Projekte...")
            
            cursor.execute("""
                INSERT INTO projects (
                    name, description, project_type, status, budget,
                    address_street, address_zip, address_city,
                    owner_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                'Test-Projekt 1',
                'Ein Test-Projekt für die Entwicklung',
                'renovation',
                'active',
                50000.0,
                'Teststraße 1',
                '12345',
                'Teststadt',
                1  # Admin als Besitzer
            ))
            
            print("✅ Test-Projekte erstellt")
        
        # Prüfe Quotes
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quote_count = cursor.fetchone()[0]
        
        if quote_count == 0:
            print("📝 Erstelle Test-Quotes...")
            
            # Akzeptierte Quote erstellen
            cursor.execute("""
                INSERT INTO quotes (
                    title, description, total_amount, currency, status,
                    company_name, contact_person, phone, email,
                    project_id, service_provider_id, accepted_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'))
            """, (
                'Test-Angebot 1',
                'Ein Test-Angebot für das Projekt',
                15000.0,
                'EUR',
                'accepted',
                'Bauunternehmen Mustermann',
                'Max Mustermann',
                '+49 123 456789',
                'max@example.com',
                1,  # Projekt 1
                2,  # Service Provider
            ))
            
            print("✅ Test-Quotes erstellt")
        
        conn.commit()
        print("✅ Test-Daten erfolgreich erstellt")
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Test-Daten: {e}")
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
                   q.company_name, q.contact_person, q.phone, q.email
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
                    contractor_name, contractor_contact, contractor_phone, contractor_email,
                    progress_percentage, paid_amount, quote_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
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
                0.0,  # progress_percentage
                0.0,  # paid_amount
                quote[0]   # quote_id
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
    print("🚀 Starte Datenbank-Überprüfung und Reparatur...")
    
    # 1. Datenbank-Status überprüfen
    if not check_database_status():
        return
    
    # 2. Test-Daten erstellen falls nötig
    create_test_data()
    
    # 3. Fehlende CostPositions erstellen
    create_missing_cost_positions()
    
    # 4. Finale Überprüfung
    print("\n🔍 Finale Überprüfung...")
    check_database_status()
    
    print("\n✅ Datenbank-Überprüfung und Reparatur abgeschlossen!")
    print("💡 Sie können jetzt das Finance-Dashboard überprüfen.")

if __name__ == "__main__":
    main() 