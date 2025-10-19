#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def create_test_notification():
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Erstelle Test-Benachrichtigung
    cursor.execute('''
    INSERT INTO notifications (
        recipient_id, type, title, message, priority, 
        is_read, is_acknowledged, created_at,
        related_quote_id, related_project_id, related_milestone_id
    ) VALUES (
        77, 'quote_accepted', 'Angebot angenommen', 
        'Ihr Angebot für "Sanitär- und Heizungsinstallation" wurde vom Bauträger angenommen. Sie können nun mit der Ausführung beginnen.',
        'high', 0, 0, ?,
        1, 1, 1
    )
    ''', (datetime.now().isoformat(),))
    
    conn.commit()
    print('✅ Test-Benachrichtigung erstellt')
    
    # Prüfe ob erstellt
    cursor.execute('SELECT * FROM notifications;')
    notifications = cursor.fetchall()
    print('Notifications in DB:', notifications)
    
    conn.close()

if __name__ == "__main__":
    create_test_notification()
