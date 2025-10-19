#!/usr/bin/env python3
import sqlite3

def fix_notifications():
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Zeige aktuelle Benachrichtigungen
    cursor.execute('SELECT id, type, title FROM notifications;')
    notifications = cursor.fetchall()
    print('=== AKTUELLE BENACHRICHTIGUNGEN ===')
    for notif in notifications:
        print(f'ID: {notif[0]}, Type: {notif[1]}, Title: {notif[2]}')
    
    # Lösche die falsche Benachrichtigung
    cursor.execute("DELETE FROM notifications WHERE type = 'quote_accepted';")
    conn.commit()
    print('\n✅ Falsche Benachrichtigungen gelöscht')
    
    # Zeige nach dem Löschen
    cursor.execute('SELECT id, type, title FROM notifications;')
    notifications = cursor.fetchall()
    print('\n=== NACH DEM LÖSCHEN ===')
    for notif in notifications:
        print(f'ID: {notif[0]}, Type: {notif[1]}, Title: {notif[2]}')
    
    conn.close()

if __name__ == "__main__":
    fix_notifications()
