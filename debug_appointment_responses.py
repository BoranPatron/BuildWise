#!/usr/bin/env python3
"""
Debug-Script für Appointment Responses
"""

import sqlite3
import json
from datetime import datetime

def debug_appointment_responses():
    """Zeige alle Appointment Responses"""
    
    # Verbinde mit der Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Zeige alle Appointment Responses
        cursor.execute("""
            SELECT 
                ar.id,
                ar.appointment_id,
                ar.service_provider_id,
                ar.status,
                ar.message,
                ar.responded_at,
                u.first_name,
                u.last_name,
                u.email
            FROM appointment_responses ar
            LEFT JOIN users u ON ar.service_provider_id = u.id
            ORDER BY ar.appointment_id, ar.service_provider_id
        """)
        
        responses = cursor.fetchall()
        
        print(f"📊 Gefunden: {len(responses)} Appointment Responses")
        print()
        
        for response in responses:
            print(f"Response ID {response[0]}:")
            print(f"  - Appointment ID: {response[1]}")
            print(f"  - Service Provider ID: {response[2]}")
            print(f"  - Status: {response[3]}")
            print(f"  - Message: {response[4] or 'None'}")
            print(f"  - Responded At: {response[5] or 'None'}")
            print(f"  - Service Provider: {response[6]} {response[7]} ({response[8]})")
            print()
        
        # Zeige auch die Appointments mit ihren eingeladenen Service Providern
        cursor.execute("""
            SELECT 
                id,
                title,
                milestone_id,
                invited_service_providers,
                responses
            FROM appointments
            ORDER BY id
        """)
        
        appointments = cursor.fetchall()
        
        print(f"📋 Gefunden: {len(appointments)} Appointments")
        print()
        
        for apt in appointments:
            print(f"Appointment ID {apt[0]}: {apt[1]}")
            print(f"  - Milestone ID: {apt[2]}")
            
            # Parse invited_service_providers
            try:
                if apt[3]:
                    invited = json.loads(apt[3]) if isinstance(apt[3], str) else apt[3]
                    print(f"  - Eingeladene Service Provider: {len(invited)}")
                    for sp in invited:
                        print(f"    * ID {sp.get('id')}: {sp.get('name')} ({sp.get('email')})")
                else:
                    print(f"  - Eingeladene Service Provider: None")
            except Exception as e:
                print(f"  - Fehler beim Parsen der eingeladenen Service Provider: {e}")
            
            # Parse responses
            try:
                if apt[4]:
                    responses = json.loads(apt[4]) if isinstance(apt[4], str) else apt[4]
                    print(f"  - Responses (JSON): {len(responses)}")
                    for resp in responses:
                        print(f"    * Service Provider {resp.get('service_provider_id')}: {resp.get('status')}")
                else:
                    print(f"  - Responses (JSON): None")
            except Exception as e:
                print(f"  - Fehler beim Parsen der Responses: {e}")
            
            print()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_appointment_responses()


