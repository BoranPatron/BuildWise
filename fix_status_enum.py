#!/usr/bin/env python3
"""
Korrigiert ungültige Status-Werte in der cost_positions Tabelle
"""

import sqlite3
from datetime import datetime

def fix_status_enums():
    """Korrigiert ungültige Status-Werte"""
    
    print("🔧 Korrigiere ungültige Status-Werte in CostPosition-Tabelle...")
    
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Finde Einträge mit ungültigen Status-Werten
        cursor.execute("""
            SELECT id, title, status 
            FROM cost_positions 
            WHERE status NOT IN ('ACTIVE', 'INACTIVE', 'COMPLETED', 'CANCELLED')
        """)
        
        invalid_entries = cursor.fetchall()
        print(f"📊 Gefundene Einträge mit ungültigen Status-Werten: {len(invalid_entries)}")
        
        if invalid_entries:
            print("\n📋 Ungültige Einträge:")
            for entry in invalid_entries:
                print(f"   - ID: {entry[0]}, Titel: {entry[1]}, Status: '{entry[2]}'")
            
            # Korrigiere die Status-Werte
            corrections = {
                'active': 'ACTIVE',
                'inactive': 'INACTIVE',
                'completed': 'COMPLETED',
                'cancelled': 'CANCELLED'
            }
            
            corrected_count = 0
            for entry in invalid_entries:
                old_status = entry[2]
                new_status = corrections.get(old_status.lower())
                
                if new_status:
                    cursor.execute(
                        "UPDATE cost_positions SET status = ? WHERE id = ?",
                        (new_status, entry[0])
                    )
                    print(f"✅ Korrigiert: ID {entry[0]} von '{old_status}' zu '{new_status}'")
                    corrected_count += 1
                else:
                    print(f"⚠️ Unbekannter Status '{old_status}' für ID {entry[0]} - setze auf 'ACTIVE'")
                    cursor.execute(
                        "UPDATE cost_positions SET status = 'ACTIVE' WHERE id = ?",
                        (entry[0],)
                    )
                    corrected_count += 1
            
            conn.commit()
            print(f"\n✅ {corrected_count} Status-Einträge korrigiert")
        else:
            print("✅ Alle Status-Werte sind bereits korrekt")
        
        # Zeige finalen Zustand
        print("\n📊 Finaler Zustand:")
        cursor.execute("SELECT id, title, status FROM cost_positions")
        rows = cursor.fetchall()
        for row in rows:
            print(f"   - ID: {row[0]}, Titel: {row[1]}, Status: {row[2]}")
        
        conn.close()
        print("\n🔒 Verbindung geschlossen")
        print("✅ Korrektur abgeschlossen")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_status_enums() 