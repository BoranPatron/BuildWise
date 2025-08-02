#!/usr/bin/env python3
"""
Überprüft die documents Tabelle direkt
"""

import sqlite3
import json

def check_documents_table():
    print("🔍 Überprüfe documents Tabelle direkt...")
    
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe ob documents Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        table_exists = cursor.fetchone() is not None
        print(f"📋 Documents Tabelle existiert: {table_exists}")
        
        if table_exists:
            # Zeige Tabellenstruktur
            cursor.execute("PRAGMA table_info(documents)")
            columns = cursor.fetchall()
            print("📋 Tabellenstruktur:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Zeige alle Dokumente
            cursor.execute("SELECT * FROM documents ORDER BY id")
            documents = cursor.fetchall()
            print(f"📄 Anzahl Dokumente in Tabelle: {len(documents)}")
            
            for doc in documents:
                print(f"  📄 Dokument ID {doc[0]}: {doc}")
        
        # Prüfe Milestones und ihre Dokumente
        cursor.execute("SELECT id, title, documents, shared_document_ids FROM milestones ORDER BY id")
        milestones = cursor.fetchall()
        print(f"\n📋 Milestones und ihre Dokumente:")
        
        for milestone in milestones:
            milestone_id, title, documents, shared_docs = milestone
            print(f"  📋 Milestone {milestone_id}: {title}")
            print(f"    Documents Feld: {documents}")
            print(f"    Shared Documents Feld: {shared_docs}")
            
            # Versuche JSON zu parsen
            if documents:
                try:
                    parsed_docs = json.loads(documents)
                    print(f"    ✅ Parsed Documents: {parsed_docs}")
                except:
                    print(f"    ❌ Fehler beim Parsen der Documents")
            
            if shared_docs:
                try:
                    parsed_shared = json.loads(shared_docs)
                    print(f"    ✅ Parsed Shared Documents: {parsed_shared}")
                except:
                    print(f"    ❌ Fehler beim Parsen der Shared Documents")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    check_documents_table() 