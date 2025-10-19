#!/usr/bin/env python3
import sqlite3

def analyze_milestone_1():
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()

    print('=== MILESTONE 1 DETAILS ===')
    cursor.execute('SELECT id, title, completion_status, project_id, updated_at FROM milestones WHERE id = 1;')
    milestone = cursor.fetchone()
    if milestone:
        print(f'Milestone: {milestone[0]} - {milestone[1]}')
        print(f'Status: {milestone[2]}')
        print(f'Projekt ID: {milestone[3]}')
        print(f'Updated: {milestone[4]}')

        print('\n=== PROJEKT DETAILS ===')
        # Prüfe welche Spalten in projects existieren
        cursor.execute('PRAGMA table_info(projects);')
        project_columns = cursor.fetchall()
        print('Verfügbare Spalten in projects:')
        for col in project_columns:
            print(f'  {col[1]} ({col[2]})')

        cursor.execute('SELECT * FROM projects WHERE id = ?;', (milestone[3],))
        project = cursor.fetchone()
        if project:
            print(f'Projekt Daten: {project}')
            # Annahme: owner_id ist die erste oder zweite Spalte
            owner_id = project[1] if len(project) > 1 else None  # Meist ist ID=0, owner_id=1
            
            if owner_id:
                print(f'Bauträger (owner_id): {owner_id}')

                print('\n=== BAUTRÄGER DETAILS ===')
                cursor.execute('SELECT id, first_name, last_name, user_role FROM users WHERE id = ?;', (owner_id,))
                bautraeger = cursor.fetchone()
                if bautraeger:
                    print(f'Bauträger: {bautraeger[0]} - {bautraeger[1]} {bautraeger[2]} ({bautraeger[3]})')

                    print('\n=== PRÜFE BENACHRICHTIGUNGEN FÜR DIESEN BAUTRÄGER ===')
                    cursor.execute('SELECT id, type, title, created_at FROM notifications WHERE recipient_id = ? ORDER BY created_at DESC;', (owner_id,))
                    notifications = cursor.fetchall()
                    if notifications:
                        for notif in notifications:
                            print(f'Benachrichtigung: {notif[0]} - {notif[1]} - {notif[2]} - {notif[3]}')
                    else:
                        print('❌ Keine Benachrichtigungen für diesen Bauträger gefunden')
                        
                        print('\n🔧 PROBLEM IDENTIFIZIERT:')
                        print(f'Milestone 1 hat Status "defects_resolved" (seit {milestone[4]})')
                        print('Aber es wurde KEINE Benachrichtigung für den Bauträger erstellt!')
                        print('Das passiert, weil die Benachrichtigungslogik erst NACH der Mängelbehebung implementiert wurde.')
                        
                        return milestone, owner_id
                else:
                    print(f'❌ Bauträger mit ID {owner_id} nicht gefunden')
            else:
                print('❌ Keine owner_id gefunden')
        else:
            print(f'❌ Projekt mit ID {milestone[3]} nicht gefunden')
    else:
        print('❌ Milestone 1 nicht gefunden')

    conn.close()
    return None, None

if __name__ == "__main__":
    milestone_info, bautraeger_id = analyze_milestone_1()
    
    if milestone_info and bautraeger_id:
        print(f'\n💡 LÖSUNG:')
        print(f'Ich kann nachträglich eine Benachrichtigung für Milestone {milestone_info[0]} erstellen')
        print(f'Empfänger: Bauträger {bautraeger_id}')
        print(f'Oder Sie melden die Mängelbehebung erneut, um die neue Logik zu testen.')
