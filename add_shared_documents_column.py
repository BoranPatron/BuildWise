#!/usr/bin/env python3
"""
Migration: Füge shared_document_ids Spalte zur milestones Tabelle hinzu
"""

import sqlite3
import json
from datetime import datetime

def add_shared_documents_column():
    """Fügt die shared_document_ids Spalte zur milestones Tabelle hinzu"""
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # Prüfe ob die Spalte bereits existiert
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'shared_document_ids' not in columns:
            print("🔄 Füge shared_document_ids Spalte zur milestones Tabelle hinzu...")
            
            # Füge die neue Spalte hinzu
            cursor.execute("""
                ALTER TABLE milestones 
                ADD COLUMN shared_document_ids TEXT DEFAULT NULL
            """)
            
            print("✅ Spalte shared_document_ids erfolgreich hinzugefügt!")
            
            # Zeige die aktualisierte Tabellenstruktur
            cursor.execute("PRAGMA table_info(milestones)")
            columns = cursor.fetchall()
            
            print("\n📋 Aktualisierte Tabellenstruktur:")
            for col in columns:
                if col[1] == 'shared_document_ids':
                    print(f"  ✨ {col[1]} ({col[2]}) - NEU")
                else:
                    print(f"     {col[1]} ({col[2]})")
        else:
            print("ℹ️  Spalte shared_document_ids existiert bereits!")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starte Migration für shared_document_ids...")
    add_shared_documents_column()
    print("✅ Migration abgeschlossen!") 