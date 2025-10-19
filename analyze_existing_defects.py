#!/usr/bin/env python3
import sqlite3

def analyze_existing_defects():
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()

    print('=== MILESTONES MIT defects_resolved STATUS ===')
    cursor.execute('SELECT id, title, completion_status, updated_at FROM milestones WHERE completion_status = "defects_resolved" ORDER BY updated_at DESC;')
    defects_resolved = cursor.fetchall()
    
    if defects_resolved:
        for milestone in defects_resolved:
            print(f'Milestone {milestone[0]}: {milestone[1]} - Status: {milestone[2]} - Updated: {milestone[3]}')
            
            # Hole Projekt-Info für diesen Milestone
            cursor.execute('SELECT project_id FROM milestones WHERE id = ?;', (milestone[0],))
            project_result = cursor.fetchone()
            if project_result:
                project_id = project_result[0]
                cursor.execute('SELECT owner_id, title FROM projects WHERE id = ?;', (project_id,))
                project_info = cursor.fetchone()
                if project_info:
                    print(f'  → Projekt {project_id}: {project_info[1]} (Bauträger: {project_info[0]})')
    else:
        print('❌ Keine Milestones mit defects_resolved Status gefunden')

    print('\n=== BENACHRICHTIGUNGEN FÜR defects_resolved ===')
    cursor.execute('SELECT id, recipient_id, type, title, created_at FROM notifications WHERE type = "defects_resolved" ORDER BY created_at DESC;')
    notifications = cursor.fetchall()
    if notifications:
        for notif in notifications:
            print(f'ID: {notif[0]}, Recipient: {notif[1]}, Type: {notif[2]}, Title: {notif[3]}, Created: {notif[4]}')
    else:
        print('❌ Keine defects_resolved Benachrichtigungen gefunden')

    print('\n=== ALLE BENACHRICHTIGUNGEN (letzte 10) ===')
    cursor.execute('SELECT id, recipient_id, type, title, created_at FROM notifications ORDER BY created_at DESC LIMIT 10;')
    all_notifications = cursor.fetchall()
    for notif in all_notifications:
        print(f'ID: {notif[0]}, Recipient: {notif[1]}, Type: {notif[2]}, Title: {notif[3]}, Created: {notif[4]}')

    conn.close()
    
    return defects_resolved

if __name__ == "__main__":
    existing_defects = analyze_existing_defects()
    
    if existing_defects:
        print(f'\n🔧 LÖSUNG: {len(existing_defects)} bestehende Mängelbehebung(en) gefunden!')
        print('Diese haben keine Benachrichtigung, da sie vor der Implementierung gemeldet wurden.')
        print('Optionen:')
        print('1. Nochmal eine neue Mängelbehebung melden (empfohlen)')
        print('2. Nachträglich Benachrichtigungen für bestehende Mängelbehebungen erstellen')
    else:
        print('\n❓ Keine bestehenden Mängelbehebungen gefunden.')
