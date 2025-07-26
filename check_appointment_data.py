import sqlite3
import json

# Verbinde zur Datenbank
conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()

print("🔍 Prüfe Appointment 13:")
cursor.execute('SELECT id, invited_service_providers, responses FROM appointments WHERE id = 13')
result = cursor.fetchone()

if result:
    apt_id, invited_providers, responses = result
    print(f"📊 Appointment {apt_id}:")
    print(f"   invited_service_providers: {invited_providers}")
    print(f"   responses: {responses}")
    
    # Prüfe appointment_responses Tabelle
    print("\n🔍 Prüfe appointment_responses Tabelle:")
    cursor.execute('SELECT * FROM appointment_responses WHERE appointment_id = 13')
    response_records = cursor.fetchall()
    
    if response_records:
        print(f"📊 Gefunden {len(response_records)} Antworten:")
        for record in response_records:
            print(f"   {record}")
    else:
        print("❌ Keine Antworten in appointment_responses Tabelle gefunden")
        
    # Prüfe alle appointments für Bauträger User 4
    print("\n🔍 Prüfe alle Appointments für User 4:")
    cursor.execute('SELECT id, title, invited_service_providers, responses FROM appointments WHERE created_by = 4')
    all_appointments = cursor.fetchall()
    
    for apt in all_appointments:
        print(f"📅 Appointment {apt[0]}: {apt[1]}")
        print(f"   invited_service_providers: {apt[2]}")
        print(f"   responses: {apt[3]}")
        print()
else:
    print("❌ Appointment 13 nicht gefunden")

conn.close() 