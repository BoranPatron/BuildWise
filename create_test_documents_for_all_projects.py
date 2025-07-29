#!/usr/bin/env python3
"""
Erstellt Test-Dokumente für alle Projekte, damit das DMS immer Dokumente anzeigt
"""

import sqlite3
import os
import uuid
from datetime import datetime

def create_test_documents():
    """Erstellt Test-Dokumente für alle Projekte"""
    
    print("🚀 Erstelle Test-Dokumente für alle Projekte...")
    
    # Verbinde zur Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Hole alle Projekte
    cursor.execute("SELECT id, name FROM projects ORDER BY id")
    projects = cursor.fetchall()
    
    print(f"📋 Gefundene Projekte: {len(projects)}")
    
    for project_id, project_name in projects:
        print(f"\n🔧 Erstelle Test-Dokumente für Projekt {project_id}: {project_name}")
        
        # Prüfe ob Projekt bereits Dokumente hat
        cursor.execute("SELECT COUNT(*) FROM documents WHERE project_id = ?", (project_id,))
        existing_docs = cursor.fetchone()[0]
        
        if existing_docs > 0:
            print(f"  ⏭️  Projekt {project_id} hat bereits {existing_docs} Dokumente - überspringe")
            continue
        
        # Erstelle Projekt-Verzeichnis
        project_dir = f"storage/uploads/project_{project_id}"
        os.makedirs(project_dir, exist_ok=True)
        
        # Erstelle verschiedene Test-Dokumente
        test_documents = [
            {
                'title': f'Bauplan - {project_name}',
                'description': f'Grundriss und Bauzeichnungen für {project_name}',
                'document_type': 'PLAN',
                'category': 'PLANNING',
                'subcategory': 'Baupläne',
                'filename': f'bauplan_{project_id}.pdf',
                'content': f'Test PDF Inhalt für Bauplan von {project_name}'
            },
            {
                'title': f'Kostenvoranschlag - {project_name}',
                'description': f'Detaillierter Kostenvoranschlag für {project_name}',
                'document_type': 'QUOTE',
                'category': 'FINANCE',
                'subcategory': 'Kostenvoranschläge',
                'filename': f'kostenvoranschlag_{project_id}.pdf',
                'content': f'Test PDF Inhalt für Kostenvoranschlag von {project_name}'
            },
            {
                'title': f'Baugenehmigung - {project_name}',
                'description': f'Offizielle Baugenehmigung für {project_name}',
                'document_type': 'PERMIT',
                'category': 'PLANNING',
                'subcategory': 'Genehmigungen',
                'filename': f'baugenehmigung_{project_id}.pdf',
                'content': f'Test PDF Inhalt für Baugenehmigung von {project_name}'
            }
        ]
        
        for i, doc in enumerate(test_documents):
            # Erstelle Datei
            file_path = os.path.join(project_dir, doc['filename'])
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc['content'])
            
            # Erstelle Datenbank-Eintrag
            cursor.execute("""
                INSERT INTO documents (
                    project_id, title, description, document_type, category, subcategory,
                    file_name, file_path, file_size, mime_type, uploaded_by,
                    created_at, updated_at, tags, is_public
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                doc['title'],
                doc['description'],
                doc['document_type'],
                doc['category'],
                doc['subcategory'],
                doc['filename'],
                file_path,
                len(doc['content']),
                'application/pdf',
                1,  # Admin User
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                f'test,dokument,{project_name.lower().replace(" ", "_")}',
                True
            ))
            
            print(f"  ✅ Dokument {i+1}: {doc['title']}")
    
    # Commit Änderungen
    conn.commit()
    
    # Zeige Zusammenfassung
    print(f"\n📊 Zusammenfassung:")
    cursor.execute("SELECT project_id, COUNT(*) FROM documents GROUP BY project_id")
    project_stats = cursor.fetchall()
    
    for project_id, doc_count in project_stats:
        cursor.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        project_name = cursor.fetchone()[0]
        print(f"  - Projekt {project_id} ({project_name}): {doc_count} Dokumente")
    
    conn.close()
    
    print(f"\n✅ Test-Dokumente erfolgreich erstellt!")
    print(f"🎯 Nächste Schritte:")
    print(f"  1. Frontend neu laden")
    print(f"  2. Jedes Projekt sollte jetzt Dokumente anzeigen")
    print(f"  3. DMS funktioniert für alle Projekte")

if __name__ == "__main__":
    create_test_documents()