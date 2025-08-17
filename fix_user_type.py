#!/usr/bin/env python3
"""
Korrigiert den user_type von User 12 zu SERVICE_PROVIDER
"""

import sqlite3
import sys

def fix_user_type():
    try:
        # Verbinde mit der Datenbank
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Zeige aktuellen Status
        cursor.execute('SELECT id, email, user_type, first_name, last_name FROM users WHERE id = 12')
        user = cursor.fetchone()
        print(f"Aktueller User: {user}")
        
        if user:
            print(f"Aktueller user_type: {user[2]}")
            
            # Update user_type zu SERVICE_PROVIDER
            cursor.execute('UPDATE users SET user_type = "SERVICE_PROVIDER" WHERE id = 12')
            conn.commit()
            print("✅ User-Type aktualisiert zu SERVICE_PROVIDER")
            
            # Zeige neuen Status
            cursor.execute('SELECT id, email, user_type, first_name, last_name FROM users WHERE id = 12')
            updated_user = cursor.fetchone()
            print(f"Aktualisierter User: {updated_user}")
            print(f"Neuer user_type: {updated_user[2]}")
        else:
            print("❌ User mit ID 12 nicht gefunden!")
            
        conn.close()
        print("\n✅ Datenbank-Update erfolgreich abgeschlossen!")
        print("🔄 Bitte starten Sie das Backend neu, damit die Änderungen wirksam werden.")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_user_type()
