#!/usr/bin/env python3
"""
Prüft subcategories für alle Dokumente
"""

import sqlite3

def check_subcategories():
    """Prüft subcategories für alle Dokumente"""
    
    print("🔍 Prüfe subcategories für alle Dokumente...")
    
    # Verbinde zur Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Hole alle Dokumente
    cursor.execute("SELECT id, title, category, subcategory FROM documents ORDER BY id")
    all_docs = cursor.fetchall()
    
    print(f"📋 Alle Dokumente ({len(all_docs)}):")
    for doc_id, title, category, subcategory in all_docs:
        status = "✅" if subcategory else "❌"
        print(f"  {status} ID {doc_id}: {title}")
        print(f"    Category: {category} | Subcategory: {subcategory}")
    
    # Prüfe Dokumente ohne subcategory
    cursor.execute("SELECT id, title, category, subcategory FROM documents WHERE subcategory IS NULL OR subcategory = ''")
    docs_without_subcategory = cursor.fetchall()
    
    print(f"\n⚠️  Dokumente ohne subcategory: {len(docs_without_subcategory)}")
    for doc_id, title, category, subcategory in docs_without_subcategory:
        print(f"  - ID {doc_id}: {title} | Category: {category}")
    
    conn.close()
    
    return len(docs_without_subcategory)

if __name__ == "__main__":
    missing_count = check_subcategories()
    
    if missing_count > 0:
        print(f"\n🔧 {missing_count} Dokumente benötigen subcategories!")
        print("Führe fix_document_subcategories.py aus...")
    else:
        print(f"\n✅ Alle Dokumente haben subcategories!")