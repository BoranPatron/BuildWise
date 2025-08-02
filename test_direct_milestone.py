#!/usr/bin/env python3
"""
Testet direkt die Milestone-Daten aus der Datenbank
"""

import sqlite3
import json

def test_direct_milestone():
    print("🔍 Teste direkt Milestone-Daten aus der Datenbank...")
    
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Teste Milestone 1
        print("\n📋 Teste Milestone 1 (TEST_Bodenlegen):")
        cursor.execute("SELECT id, title, documents, shared_document_ids FROM milestones WHERE id = 1")
        milestone = cursor.fetchone()
        
        if milestone:
            milestone_id, title, documents, shared_docs = milestone
            print(f"✅ Milestone gefunden: {title}")
            print(f"📄 Documents Feld: {documents}")
            print(f"📄 Shared Documents Feld: {shared_docs}")
            
            # Parse shared_document_ids
            if shared_docs:
                try:
                    shared_ids = json.loads(shared_docs)
                    print(f"✅ Parsed Shared IDs: {shared_ids}")
                    
                    # Lade die Dokumente
                    if shared_ids:
                        placeholders = ','.join(['?' for _ in shared_ids])
                        cursor.execute(f"SELECT id, title, file_name, mime_type, file_size FROM documents WHERE id IN ({placeholders})", shared_ids)
                        docs = cursor.fetchall()
                        print(f"📄 Gefundene Dokumente: {len(docs)}")
                        for doc in docs:
                            print(f"  📄 ID {doc[0]}: {doc[1]} ({doc[2]}) - {doc[3]} - {doc[4]} bytes")
                except Exception as e:
                    print(f"❌ Fehler beim Parsen: {e}")
        
        # Teste Milestone 2
        print("\n📋 Teste Milestone 2 (tet):")
        cursor.execute("SELECT id, title, documents, shared_document_ids FROM milestones WHERE id = 2")
        milestone = cursor.fetchone()
        
        if milestone:
            milestone_id, title, documents, shared_docs = milestone
            print(f"✅ Milestone gefunden: {title}")
            print(f"📄 Documents Feld: {documents}")
            print(f"📄 Shared Documents Feld: {shared_docs}")
            
            # Parse shared_document_ids
            if shared_docs:
                try:
                    shared_ids = json.loads(shared_docs)
                    print(f"✅ Parsed Shared IDs: {shared_ids}")
                    
                    # Lade die Dokumente
                    if shared_ids:
                        placeholders = ','.join(['?' for _ in shared_ids])
                        cursor.execute(f"SELECT id, title, file_name, mime_type, file_size FROM documents WHERE id IN ({placeholders})", shared_ids)
                        docs = cursor.fetchall()
                        print(f"📄 Gefundene Dokumente: {len(docs)}")
                        for doc in docs:
                            print(f"  📄 ID {doc[0]}: {doc[1]} ({doc[2]}) - {doc[3]} - {doc[4]} bytes")
                except Exception as e:
                    print(f"❌ Fehler beim Parsen: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_direct_milestone() 