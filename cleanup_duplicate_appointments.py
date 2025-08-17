#!/usr/bin/env python3
"""
Bereinige doppelte Appointments in der Datenbank
Behält nur den ältesten Appointment pro Milestone und löscht die Duplikate
"""

import sqlite3
import json
from datetime import datetime

def cleanup_duplicate_appointments():
    """Bereinige doppelte Appointments"""
    
    # Verbinde mit der Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Finde alle Appointments gruppiert nach milestone_id
        cursor.execute("""
            SELECT 
                milestone_id,
                COUNT(*) as count,
                GROUP_CONCAT(id) as appointment_ids,
                GROUP_CONCAT(created_at) as created_dates
            FROM appointments
            WHERE milestone_id IS NOT NULL
            GROUP BY milestone_id
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("✅ Keine doppelten Appointments gefunden")
            return
        
        print(f"⚠️ Gefunden: {len(duplicates)} Milestones mit doppelten Appointments")
        
        for milestone_id, count, appointment_ids_str, created_dates_str in duplicates:
            appointment_ids = [int(id) for id in appointment_ids_str.split(',')]
            created_dates = created_dates_str.split(',')
            
            print(f"\n📋 Milestone {milestone_id}: {count} Appointments")
            print(f"   IDs: {appointment_ids}")
            
            # Behalte den ältesten (ersten) Appointment
            keep_id = appointment_ids[0]
            delete_ids = appointment_ids[1:]
            
            print(f"   ✅ Behalte: ID {keep_id}")
            print(f"   ❌ Lösche: IDs {delete_ids}")
            
            # Lösche die Duplikate
            for delete_id in delete_ids:
                # Lösche auch zugehörige appointment_responses
                cursor.execute("""
                    DELETE FROM appointment_responses 
                    WHERE appointment_id = ?
                """, (delete_id,))
                
                # Lösche den Appointment
                cursor.execute("""
                    DELETE FROM appointments 
                    WHERE id = ?
                """, (delete_id,))
            
            conn.commit()
            print(f"   ✅ {len(delete_ids)} Duplikate gelöscht")
        
        print("\n✅ Bereinigung abgeschlossen")
        
        # Zeige aktuelle Appointments
        cursor.execute("""
            SELECT 
                id,
                milestone_id,
                title,
                status,
                created_at
            FROM appointments
            ORDER BY milestone_id, created_at
        """)
        
        print("\n📊 Aktuelle Appointments:")
        for row in cursor.fetchall():
            print(f"   ID {row[0]}: Milestone {row[1]} - {row[2]} ({row[3]})")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_duplicate_appointments()
