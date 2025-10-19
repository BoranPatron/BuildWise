#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def create_test_notification():
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Lösche alte Test-Benachrichtigungen
        cursor.execute("DELETE FROM notifications WHERE type = 'quote_accepted'")
        
        # Erstelle Test-Benachrichtigung
        now = datetime.now().isoformat()
        cursor.execute('''
        INSERT INTO notifications (
            recipient_id, type, title, message, priority, 
            is_read, is_acknowledged, created_at,
            related_quote_id, related_project_id, related_milestone_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            77, 'quote_accepted', 'Angebot angenommen', 
            'Ihr Angebot für "Sanitär- und Heizungsinstallation" wurde vom Bauträger angenommen. Sie können nun mit der Ausführung beginnen.',
            'high', 0, 0, now, 1, 1, 1
        ))
        
        conn.commit()
        print('✅ Test-Benachrichtigung erstellt')
        
        # Prüfe ob erstellt
        cursor.execute('SELECT id, recipient_id, type, title, is_acknowledged FROM notifications;')
        notifications = cursor.fetchall()
        print('Notifications in DB:')
        for notif in notifications:
            print(f"  ID: {notif[0]}, Recipient: {notif[1]}, Type: {notif[2]}, Title: {notif[3]}, Acknowledged: {notif[4]}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_test_notification()
