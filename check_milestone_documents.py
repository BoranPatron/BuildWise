#!/usr/bin/env python3
"""
Prüft Milestone-Dokumente in der Datenbank und erstellt Testdaten
"""

import sqlite3
import json
from datetime import datetime

def check_milestone_documents():
    """Prüft vorhandene Dokumente in Milestones"""
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        print("🔍 Prüfe Milestone-Dokumente...")
        
        # Prüfe ob documents Spalte existiert
        cursor.execute("PRAGMA table_info(milestones)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'documents' not in columns:
            print("❌ documents Spalte existiert nicht in milestones Tabelle!")
            return
        
        print("✅ documents Spalte existiert")
        
        # Prüfe alle Milestones
        cursor.execute("SELECT id, title, documents FROM milestones")
        milestones = cursor.fetchall()
        
        print(f"📊 Gefunden: {len(milestones)} Milestones")
        
        milestones_with_docs = 0
        for milestone_id, title, documents in milestones:
            if documents and documents != 'null' and documents != '[]':
                milestones_with_docs += 1
                print(f"📄 Milestone {milestone_id} ({title}): {documents}")
        
        print(f"📄 Milestones mit Dokumenten: {milestones_with_docs}")
        
        if milestones_with_docs == 0:
            print("🔧 Erstelle Testdokumente für erstes Milestone...")
            create_test_documents(cursor, conn)
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        conn.close()

def create_test_documents(cursor, conn):
    """Erstellt Testdokumente für das erste Milestone"""
    try:
        # Hole das erste Milestone
        cursor.execute("SELECT id, title FROM milestones LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            print("❌ Keine Milestones gefunden!")
            return
            
        milestone_id, title = result
        
        # Erstelle Testdokumente
        test_documents = [
            {
                "id": "doc_1",
                "name": "Leistungsverzeichnis_Elektro.pdf",
                "url": "/storage/uploads/project_1/Leistungsverzeichnis_Elektro.pdf",
                "type": "application/pdf",
                "size": 2048576,  # 2MB
                "uploaded_at": datetime.now().isoformat()
            },
            {
                "id": "doc_2", 
                "name": "Bauinformationen_Projekt.docx",
                "url": "/storage/uploads/project_1/Bauinformationen_Projekt.docx",
                "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "size": 1024000,  # 1MB
                "uploaded_at": datetime.now().isoformat()
            },
            {
                "id": "doc_3",
                "name": "Technische_Spezifikation.pptx", 
                "url": "/storage/uploads/project_1/Technische_Spezifikation.pptx",
                "type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "size": 3072000,  # 3MB
                "uploaded_at": datetime.now().isoformat()
            }
        ]
        
        # Aktualisiere das Milestone mit Testdokumenten
        cursor.execute(
            "UPDATE milestones SET documents = ? WHERE id = ?",
            (json.dumps(test_documents), milestone_id)
        )
        
        conn.commit()
        
        print(f"✅ Testdokumente für Milestone {milestone_id} ({title}) erstellt:")
        for doc in test_documents:
            print(f"   📄 {doc['name']} ({doc['type']})")
            
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Testdokumente: {e}")

if __name__ == "__main__":
    check_milestone_documents() 