#!/usr/bin/env python3
"""
Debug-Script für Quote Service Provider IDs
"""

import sqlite3
import json
from datetime import datetime

def debug_quotes_service_providers():
    """Zeige alle Quotes mit ihren Service Provider IDs"""
    
    # Verbinde mit der Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Zeige alle Quotes mit Service Provider Details
        cursor.execute("""
            SELECT 
                q.id as quote_id,
                q.milestone_id,
                q.service_provider_id,
                q.status,
                q.total_amount,
                q.company_name,
                u.id as user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.user_role
            FROM quotes q
            LEFT JOIN users u ON q.service_provider_id = u.id
            ORDER BY q.milestone_id, q.id
        """)
        
        quotes = cursor.fetchall()
        
        print(f"📊 Gefunden: {len(quotes)} Quotes")
        print()
        
        milestone_groups = {}
        for quote in quotes:
            milestone_id = quote[1]
            if milestone_id not in milestone_groups:
                milestone_groups[milestone_id] = []
            milestone_groups[milestone_id].append(quote)
        
        for milestone_id, quotes_in_milestone in milestone_groups.items():
            print(f"🏗️ Milestone {milestone_id}: {len(quotes_in_milestone)} Quotes")
            
            for quote in quotes_in_milestone:
                print(f"  Quote ID {quote[0]}:")
                print(f"    - Service Provider ID: {quote[2]}")
                print(f"    - Status: {quote[3]}")
                print(f"    - Company Name: {quote[5] or 'None'}")
                print(f"    - Total Amount: {quote[4] or 0}")
                
                if quote[6]:  # user_id exists
                    print(f"    - User: {quote[7]} {quote[8]} ({quote[9]})")
                    print(f"    - User Role: {quote[10]}")
                else:
                    print(f"    - ❌ KEIN USER GEFUNDEN für Service Provider ID {quote[2]}")
                print()
            
            print("-" * 50)
        
        # Zeige alle Users mit DIENSTLEISTER Rolle
        print("\n👥 Alle DIENSTLEISTER Users:")
        cursor.execute("""
            SELECT 
                id,
                first_name,
                last_name,
                email,
                user_role,
                user_type
            FROM users
            WHERE user_role = 'DIENSTLEISTER'
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        for user in users:
            print(f"  User ID {user[0]}: {user[1]} {user[2]} ({user[3]})")
            print(f"    - Role: {user[4]}, Type: {user[5]}")
        
        print()
        
        # Prüfe auf falsche Service Provider IDs in Quotes
        print("🔍 Analyse der Service Provider ID Zuordnungen:")
        
        cursor.execute("""
            SELECT DISTINCT service_provider_id FROM quotes WHERE service_provider_id IS NOT NULL
        """)
        used_sp_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT id FROM users WHERE user_role = 'DIENSTLEISTER'
        """)
        valid_sp_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"  - Verwendete Service Provider IDs in Quotes: {used_sp_ids}")
        print(f"  - Gültige DIENSTLEISTER User IDs: {valid_sp_ids}")
        
        invalid_ids = [sp_id for sp_id in used_sp_ids if sp_id not in valid_sp_ids]
        if invalid_ids:
            print(f"  - ❌ UNGÜLTIGE Service Provider IDs: {invalid_ids}")
        else:
            print(f"  - ✅ Alle Service Provider IDs sind gültig")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_quotes_service_providers()


