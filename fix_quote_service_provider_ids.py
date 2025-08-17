#!/usr/bin/env python3
"""
Korrigiere falsche Service Provider IDs in Quotes basierend auf company_name
"""

import sqlite3
import json

def fix_quote_service_provider_ids():
    """Korrigiere Service Provider IDs basierend auf company_name"""
    
    # Verbinde mit der Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Zeige aktuelle Situation
        cursor.execute("""
            SELECT 
                q.id,
                q.service_provider_id,
                q.company_name,
                q.milestone_id,
                u.first_name,
                u.last_name,
                u.email
            FROM quotes q
            LEFT JOIN users u ON q.service_provider_id = u.id
            ORDER BY q.id
        """)
        
        quotes = cursor.fetchall()
        
        print("📊 Aktuelle Quote-Zuordnungen:")
        for quote in quotes:
            print(f"  Quote {quote[0]}: company_name='{quote[2]}' -> service_provider_id={quote[1]} ({quote[4]} {quote[5]})")
        print()
        
        # Mapping basierend auf den Console-Logs:
        # - PietiboyAG sollte zu User ID 6 (Stephan Schellworth)
        # - BaccoGMBH sollte zu User ID 7 (steve schelli)
        
        # Hole alle DIENSTLEISTER
        cursor.execute("""
            SELECT id, first_name, last_name, email FROM users WHERE user_role = 'DIENSTLEISTER'
        """)
        dienstleister = cursor.fetchall()
        
        print("👥 Verfügbare DIENSTLEISTER:")
        for dl in dienstleister:
            print(f"  ID {dl[0]}: {dl[1]} {dl[2]} ({dl[3]})")
        print()
        
        # Korrigiere basierend auf company_name
        corrections = []
        
        for quote in quotes:
            quote_id, current_sp_id, company_name = quote[0], quote[1], quote[2]
            
            if company_name == "BaccoGMBH" and current_sp_id == 6:
                # BaccoGMBH sollte User ID 7 sein (steve schelli)
                corrections.append((quote_id, 7, company_name))
                print(f"🔧 Korrektur geplant: Quote {quote_id} (BaccoGMBH) von ID {current_sp_id} zu ID 7")
            
            elif company_name == "PietiboyAG" and current_sp_id == 6:
                # PietiboyAG bleibt bei User ID 6 (Stephan Schellworth)
                print(f"✅ Quote {quote_id} (PietiboyAG) bleibt bei ID {current_sp_id}")
            
            else:
                print(f"❓ Quote {quote_id} ({company_name}) - keine Korrektur definiert")
        
        print()
        
        if corrections:
            print(f"🔧 Führe {len(corrections)} Korrekturen durch:")
            
            for quote_id, new_sp_id, company_name in corrections:
                cursor.execute("""
                    UPDATE quotes 
                    SET service_provider_id = ? 
                    WHERE id = ?
                """, (new_sp_id, quote_id))
                
                print(f"  ✅ Quote {quote_id} ({company_name}) -> Service Provider ID {new_sp_id}")
            
            conn.commit()
            print("\n✅ Alle Korrekturen erfolgreich angewendet!")
            
            # Zeige neue Situation
            print("\n📊 Neue Quote-Zuordnungen:")
            cursor.execute("""
                SELECT 
                    q.id,
                    q.service_provider_id,
                    q.company_name,
                    u.first_name,
                    u.last_name,
                    u.email
                FROM quotes q
                LEFT JOIN users u ON q.service_provider_id = u.id
                ORDER BY q.id
            """)
            
            new_quotes = cursor.fetchall()
            for quote in new_quotes:
                print(f"  Quote {quote[0]}: company_name='{quote[2]}' -> service_provider_id={quote[1]} ({quote[3]} {quote[4]})")
        
        else:
            print("ℹ️ Keine Korrekturen erforderlich")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_quote_service_provider_ids()


