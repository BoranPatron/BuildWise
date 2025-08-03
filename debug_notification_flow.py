#!/usr/bin/env python3
import sqlite3
import requests
import json
from datetime import datetime, timedelta

def debug_notification_flow():
    print("🔍 Debug: Kompletter Notification-Flow")
    print("=" * 50)
    
    # 1. Database Check
    print("\n📋 1. DATABASE CHECK")
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Users
    cursor.execute('SELECT id, first_name, last_name, user_type, email FROM users WHERE id IN (4, 6)')
    users = cursor.fetchall()
    print("👥 Test Users:")
    for user in users:
        print(f"  User {user[0]}: {user[1]} {user[2]} ({user[3]}) - {user[4]}")
    
    # Projects
    cursor.execute('SELECT id, name, owner_id FROM projects')
    projects = cursor.fetchall()
    print(f"\n🏗️ Projekte ({len(projects)}):")
    for project in projects:
        print(f"  Projekt {project[0]}: {project[1]} (Besitzer: User {project[2]})")
    
    # Milestones
    cursor.execute('SELECT id, title, project_id FROM milestones')
    milestones = cursor.fetchall()
    print(f"\n📍 Milestones ({len(milestones)}):")
    for milestone in milestones:
        print(f"  Milestone {milestone[0]}: {milestone[1]} (Projekt {milestone[2]})")
    
    # Progress Updates (letzten 7 Tage)
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cursor.execute('''
        SELECT mp.id, mp.user_id, mp.milestone_id, mp.message, mp.created_at,
               u.first_name, u.user_type, m.title, p.name
        FROM milestone_progress mp
        JOIN users u ON mp.user_id = u.id
        JOIN milestones m ON mp.milestone_id = m.id
        JOIN projects p ON m.project_id = p.id
        WHERE mp.created_at > ?
        ORDER BY mp.created_at DESC
    ''', (week_ago,))
    
    updates = cursor.fetchall()
    print(f"\n💬 Progress Updates (letzte 7 Tage: {len(updates)}):")
    for update in updates:
        print(f"  Update {update[0]}: User {update[1]} ({update[5]}, {update[6]})")
        print(f"    Message: \"{update[3][:50]}...\"")
        print(f"    Milestone: {update[7]} (Projekt: {update[8]})")
        print(f"    Date: {update[4]}")
        print("    ---")
    
    conn.close()
    
    # 2. API Tests
    print("\n🔌 2. API TESTS")
    base_url = "http://localhost:8000"
    
    # Test Health
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"✅ Backend läuft: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {e}")
        return
    
    # Test mit echten Tokens (simuliert)
    print("\n🔑 3. TOKEN SIMULATION")
    print("Für echten Test müssen Sie sich im Frontend einloggen und die Benachrichtigungslasche öffnen.")
    print("Schauen Sie in der Browser-Console nach folgenden Logs:")
    print("  🔄 NotificationTab: Lade Progress Updates für...")
    print("  🔍 NotificationTab: Projekte geladen: X")
    print("  🔍 NotificationTab: Progress Updates geladen: X")
    
    # 4. Expected Notifications
    print("\n📊 4. ERWARTETE BENACHRICHTIGUNGEN")
    
    # Für User 4 (Bauträger)
    user_4_updates = [u for u in updates if u[1] != 4]  # Updates von anderen
    print(f"👤 User 4 (Bauträger) sollte {len(user_4_updates)} Benachrichtigungen sehen:")
    for update in user_4_updates[:3]:  # Erste 3
        print(f"  - Von User {update[1]} ({update[6]}): \"{update[3][:30]}...\"")
    
    # Für User 6 (Dienstleister)
    user_6_updates = [u for u in updates if u[1] != 6]  # Updates von anderen
    print(f"👤 User 6 (Dienstleister) sollte {len(user_6_updates)} Benachrichtigungen sehen:")
    for update in user_6_updates[:3]:  # Erste 3
        print(f"  - Von User {update[1]} ({update[6]}): \"{update[3][:30]}...\"")
    
    # 5. Troubleshooting
    print("\n🔧 5. TROUBLESHOOTING STEPS")
    print("1. Backend läuft: ✅" if response.status_code == 200 else "1. Backend läuft: ❌")
    print("2. Frontend öffnen: http://localhost:5173")
    print("3. Als Bauträger einloggen (User 4)")
    print("4. F12 drücken → Console öffnen")
    print("5. Benachrichtigungslasche rechts öffnen")
    print("6. Console-Logs prüfen:")
    print("   - 'NotificationTab: Projekte geladen: X' (sollte > 0 sein)")
    print("   - 'NotificationTab: Progress Updates geladen: X' (sollte > 0 sein)")
    print("7. Als Dienstleister einloggen (User 6) und wiederholen")
    print("8. Nachricht senden und prüfen ob andere User sie nach 10s sieht")

if __name__ == "__main__":
    debug_notification_flow()