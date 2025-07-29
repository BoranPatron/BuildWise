#!/usr/bin/env python3
"""
Migration: PDF document_type und ORDER_CONFIRMATIONS Kategorie hinzufügen
"""

import sqlite3
import os
from datetime import datetime

def add_pdf_document_type_and_order_confirmations():
    """Fügt PDF document_type und ORDER_CONFIRMATIONS Kategorie hinzu"""
    
    # Datenbankpfad
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank nicht gefunden:", db_path)
        return False
    
    try:
        # Verbinde zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Starte Migration: PDF document_type und ORDER_CONFIRMATIONS Kategorie...")
        
        # Prüfe aktuelle document_type Werte
        cursor.execute("PRAGMA table_info(documents)")
        columns = cursor.fetchall()
        document_type_column = None
        
        for col in columns:
            if col[1] == 'document_type':
                document_type_column = col
                break
        
        if not document_type_column:
            print("❌ document_type Spalte nicht gefunden")
            return False
        
        # Prüfe aktuelle category Werte
        cursor.execute("PRAGMA table_info(documents)")
        columns = cursor.fetchall()
        category_column = None
        
        for col in columns:
            if col[1] == 'category':
                category_column = col
                break
        
        if not category_column:
            print("❌ category Spalte nicht gefunden")
            return False
        
        # Aktualisiere bestehende Dokumente mit PDF document_type
        cursor.execute("""
            UPDATE documents 
            SET document_type = 'pdf' 
            WHERE document_type = 'other' 
            AND (title LIKE '%Auftragsbestätigung%' OR title LIKE '%auftragsbestätigung%')
        """)
        
        pdf_updated = cursor.rowcount
        print(f"✅ {pdf_updated} Dokumente auf PDF document_type aktualisiert")
        
        # Aktualisiere bestehende Dokumente mit ORDER_CONFIRMATIONS Kategorie
        cursor.execute("""
            UPDATE documents 
            SET category = 'order_confirmations' 
            WHERE category = 'contracts' 
            AND (title LIKE '%Auftragsbestätigung%' OR title LIKE '%auftragsbestätigung%')
        """)
        
        category_updated = cursor.rowcount
        print(f"✅ {category_updated} Dokumente auf ORDER_CONFIRMATIONS Kategorie aktualisiert")
        
        # Zeige aktuelle Statistiken
        cursor.execute("""
            SELECT document_type, COUNT(*) as count 
            FROM documents 
            GROUP BY document_type 
            ORDER BY count DESC
        """)
        
        print("\n📊 Aktuelle document_type Verteilung:")
        for doc_type, count in cursor.fetchall():
            print(f"  - {doc_type}: {count}")
        
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM documents 
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        print("\n📊 Aktuelle category Verteilung:")
        for category, count in cursor.fetchall():
            print(f"  - {category}: {count}")
        
        # Commit Änderungen
        conn.commit()
        print("\n✅ Migration erfolgreich abgeschlossen!")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starte PDF document_type und ORDER_CONFIRMATIONS Migration...")
    success = add_pdf_document_type_and_order_confirmations()
    
    if success:
        print("✅ Migration erfolgreich!")
    else:
        print("❌ Migration fehlgeschlagen!")