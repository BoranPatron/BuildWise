#!/usr/bin/env python3
"""
Migration: Fügt has_unread_messages Spalte zur milestones Tabelle hinzu
"""

import sqlite3
import os

def add_unread_messages_column():
    """Fügt has_unread_messages Spalte zur milestones Tabelle hinzu"""
    print("Fuege has_unread_messages Spalte zur milestones Tabelle hinzu...")
    
    if not os.path.exists('buildwise.db'):
        print("Datenbank buildwise.db nicht gefunden!")
        return False
    
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'has_unread_messages' in columns:
            print("Spalte has_unread_messages existiert bereits")
            conn.close()
            return True
        
        # Füge Spalte hinzu
        cursor.execute("""
            ALTER TABLE milestones 
            ADD COLUMN has_unread_messages BOOLEAN DEFAULT FALSE
        """)
        
        # Setze alle bestehenden Milestones auf FALSE (keine ungelesenen Nachrichten)
        cursor.execute("""
            UPDATE milestones 
            SET has_unread_messages = FALSE 
            WHERE has_unread_messages IS NULL
        """)
        
        conn.commit()
        conn.close()
        
        print("Spalte has_unread_messages erfolgreich hinzugefuegt")
        return True
        
    except Exception as e:
        print(f"Fehler beim Hinzufuegen der Spalte: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    add_unread_messages_column()
