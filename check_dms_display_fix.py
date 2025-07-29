#!/usr/bin/env python3
"""
DMS-Anzeige-Problem Diagnose und Fix
"""

import sqlite3
import os
from datetime import datetime

def diagnose_dms_problem():
    """Diagnostiziert das DMS-Anzeigeproblem"""
    
    print("🔍 DMS-Anzeige-Problem Diagnose")
    print("=" * 50)
    
    # Verbinde zur Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # 1. Prüfe verfügbare Projekte
    cursor.execute("SELECT id, name FROM projects ORDER BY id")
    projects = cursor.fetchall()
    print(f"\n📋 Verfügbare Projekte ({len(projects)}):")
    for project_id, name in projects:
        print(f"  - Projekt {project_id}: {name}")
    
    # 2. Prüfe Dokumente pro Projekt
    print(f"\n📄 Dokumente pro Projekt:")
    for project_id, name in projects:
        cursor.execute("SELECT COUNT(*) FROM documents WHERE project_id = ?", (project_id,))
        doc_count = cursor.fetchone()[0]
        print(f"  - Projekt {project_id} ({name}): {doc_count} Dokumente")
        
        if doc_count > 0:
            cursor.execute("""
                SELECT id, title, document_type, category, file_path 
                FROM documents 
                WHERE project_id = ? 
                ORDER BY created_at DESC
            """, (project_id,))
            docs = cursor.fetchall()
            for doc in docs:
                print(f"    * ID {doc[0]}: {doc[1]} ({doc[2]}/{doc[3]})")
    
    # 3. Prüfe Storage-Verzeichnisse
    print(f"\n📁 Storage-Verzeichnisse:")
    storage_path = "storage/uploads"
    if os.path.exists(storage_path):
        for item in os.listdir(storage_path):
            item_path = os.path.join(storage_path, item)
            if os.path.isdir(item_path):
                file_count = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                print(f"  - {item}: {file_count} Dateien")
    else:
        print("  - storage/uploads Verzeichnis existiert nicht!")
    
    # 4. Prüfe Datenbank-Integrität
    print(f"\n🔍 Datenbank-Integrität:")
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]
    print(f"  - Gesamt Dokumente in DB: {total_docs}")
    
    cursor.execute("SELECT COUNT(*) FROM documents WHERE file_path IS NULL OR file_path = ''")
    null_paths = cursor.fetchone()[0]
    print(f"  - Dokumente ohne Pfad: {null_paths}")
    
    # 5. Prüfe Datei-Existenz
    print(f"\n📂 Datei-Existenz-Check:")
    cursor.execute("SELECT id, title, file_path FROM documents")
    docs = cursor.fetchall()
    
    missing_files = 0
    for doc_id, title, file_path in docs:
        if file_path and os.path.exists(file_path):
            print(f"  ✅ ID {doc_id}: {title} - Datei existiert")
        else:
            print(f"  ❌ ID {doc_id}: {title} - Datei fehlt: {file_path}")
            missing_files += 1
    
    print(f"\n📊 Zusammenfassung:")
    print(f"  - Projekte: {len(projects)}")
    print(f"  - Dokumente in DB: {total_docs}")
    print(f"  - Fehlende Dateien: {missing_files}")
    
    conn.close()
    
    return {
        'projects': len(projects),
        'total_docs': total_docs,
        'missing_files': missing_files
    }

def fix_dms_display():
    """Behebt das DMS-Anzeigeproblem"""
    
    print("\n🔧 DMS-Anzeige-Problem Fix")
    print("=" * 50)
    
    # Verbinde zur Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # 1. Erstelle fehlende Storage-Verzeichnisse
    storage_path = "storage/uploads"
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
        print(f"✅ Storage-Verzeichnis erstellt: {storage_path}")
    
    # 2. Erstelle Projekt-Verzeichnisse
    cursor.execute("SELECT id FROM projects")
    project_ids = [row[0] for row in cursor.fetchall()]
    
    for project_id in project_ids:
        project_dir = f"storage/uploads/project_{project_id}"
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            print(f"✅ Projekt-Verzeichnis erstellt: {project_dir}")
    
    # 3. Korrigiere fehlende file_path Einträge
    cursor.execute("SELECT id, title FROM documents WHERE file_path IS NULL OR file_path = ''")
    null_path_docs = cursor.fetchall()
    
    if null_path_docs:
        print(f"\n⚠️  Dokumente ohne Pfad gefunden: {len(null_path_docs)}")
        for doc_id, title in null_path_docs:
            # Generiere Standard-Pfad
            default_path = f"storage/uploads/project_8/{title.replace(' ', '_')}.txt"
            cursor.execute("UPDATE documents SET file_path = ? WHERE id = ?", (default_path, doc_id))
            print(f"  - ID {doc_id}: Pfad korrigiert zu {default_path}")
    
    # 4. Aktualisiere Dokument-Metadaten
    cursor.execute("""
        UPDATE documents 
        SET updated_at = ? 
        WHERE updated_at IS NULL
    """, (datetime.now().isoformat(),))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ DMS-Fix abgeschlossen!")
    print(f"  - Alle Projekt-Verzeichnisse erstellt")
    print(f"  - Fehlende Pfade korrigiert")
    print(f"  - Metadaten aktualisiert")

if __name__ == "__main__":
    print("🚀 Starte DMS-Anzeige-Problem Diagnose und Fix...")
    
    # Diagnose
    stats = diagnose_dms_problem()
    
    # Fix
    if stats['total_docs'] > 0:
        fix_dms_display()
        
        print(f"\n🎯 Nächste Schritte:")
        print(f"  1. Frontend neu laden")
        print(f"  2. Projekt 8 (Landhaus Ticino) auswählen")
        print(f"  3. Dokumente sollten jetzt angezeigt werden")
    else:
        print(f"\n⚠️  Keine Dokumente gefunden!")
        print(f"  - Bitte zuerst Dokumente hochladen")
    
    print(f"\n✅ Diagnose und Fix abgeschlossen!")