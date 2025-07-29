#!/usr/bin/env python3
"""
Migration: DMS Enhancements für SQLite
Fügt neue Felder für das erweiterte Dokumentenmanagementsystem hinzu
"""

import asyncio
import sys
import os
import sqlite3

# Pfad zum Projektverzeichnis hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def run_sqlite_migration():
    """Führt die DMS Enhancement Migration für SQLite aus"""
    
    db_path = "./buildwise.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank nicht gefunden. Bitte zuerst das Backend starten.")
        return
    
    try:
        print("🚀 Starte DMS Enhancement Migration für SQLite...")
        
        # Verbindung zur SQLite-Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe ob Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents';")
        if not cursor.fetchone():
            print("❌ Documents-Tabelle nicht gefunden")
            return
        
        # Neue Spalten hinzufügen (falls sie nicht existieren)
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN subcategory TEXT;")
            print("✅ Spalte 'subcategory' hinzugefügt")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️ Spalte 'subcategory' existiert bereits")
            else:
                print(f"⚠️ Fehler bei subcategory: {e}")
        
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN is_favorite BOOLEAN DEFAULT 0;")
            print("✅ Spalte 'is_favorite' hinzugefügt")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️ Spalte 'is_favorite' existiert bereits")
            else:
                print(f"⚠️ Fehler bei is_favorite: {e}")
        
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN status TEXT DEFAULT 'draft';")
            print("✅ Spalte 'status' hinzugefügt")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️ Spalte 'status' existiert bereits")
            else:
                print(f"⚠️ Fehler bei status: {e}")
        
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN accessed_at TIMESTAMP;")
            print("✅ Spalte 'accessed_at' hinzugefügt")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️ Spalte 'accessed_at' existiert bereits")
            else:
                print(f"⚠️ Fehler bei accessed_at: {e}")
        
        # Prüfe ob category Spalte existiert und aktualisiere Datentyp
        cursor.execute("PRAGMA table_info(documents);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category' not in columns:
            try:
                cursor.execute("ALTER TABLE documents ADD COLUMN category TEXT DEFAULT 'documentation';")
                print("✅ Spalte 'category' hinzugefügt")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Fehler bei category: {e}")
        else:
            print("ℹ️ Spalte 'category' existiert bereits")
        
        # Standardwerte für bestehende Datensätze setzen
        cursor.execute("""
            UPDATE documents 
            SET is_favorite = 0 
            WHERE is_favorite IS NULL;
        """)
        
        cursor.execute("""
            UPDATE documents 
            SET status = 'draft' 
            WHERE status IS NULL OR status = '';
        """)
        
        cursor.execute("""
            UPDATE documents 
            SET category = 'documentation' 
            WHERE category IS NULL OR category = '';
        """)
        
        # Indizes für bessere Performance erstellen
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_subcategory ON documents(subcategory);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_is_favorite ON documents(is_favorite);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_accessed_at ON documents(accessed_at);")
            print("✅ Performance-Indizes erstellt")
        except sqlite3.OperationalError as e:
            print(f"⚠️ Fehler bei Indizes: {e}")
        
        # FTS (Full-Text Search) Tabelle für bessere Suchperformance
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    title, description, tags, file_name, content='documents', content_rowid='id'
                );
            """)
            
            # Bestehende Daten in FTS-Tabelle einfügen
            cursor.execute("""
                INSERT OR REPLACE INTO documents_fts(rowid, title, description, tags, file_name)
                SELECT id, title, COALESCE(description, ''), COALESCE(tags, ''), file_name
                FROM documents;
            """)
            print("✅ Full-Text Search Tabelle erstellt und befüllt")
        except sqlite3.OperationalError as e:
            print(f"⚠️ Fehler bei FTS: {e}")
        
        # Trigger für automatische FTS-Updates
        try:
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS documents_fts_insert AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(rowid, title, description, tags, file_name)
                    VALUES (new.id, new.title, COALESCE(new.description, ''), COALESCE(new.tags, ''), new.file_name);
                END;
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS documents_fts_delete AFTER DELETE ON documents BEGIN
                    DELETE FROM documents_fts WHERE rowid = old.id;
                END;
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS documents_fts_update AFTER UPDATE ON documents BEGIN
                    UPDATE documents_fts SET 
                        title = new.title,
                        description = COALESCE(new.description, ''),
                        tags = COALESCE(new.tags, ''),
                        file_name = new.file_name
                    WHERE rowid = new.id;
                END;
            """)
            print("✅ FTS-Update Trigger erstellt")
        except sqlite3.OperationalError as e:
            print(f"⚠️ Fehler bei Triggern: {e}")
        
        # Änderungen speichern
        conn.commit()
        conn.close()
        
        print("\n✅ DMS Enhancement Migration erfolgreich abgeschlossen!")
        print("\n📋 Hinzugefügte Features:")
        print("   • Unterkategorien für flexible Organisation (subcategory)")
        print("   • Favoriten-System für wichtige Dokumente (is_favorite)")
        print("   • Status-Tracking (status: draft, review, approved, rejected, archived)")
        print("   • Zugriffs-Tracking (accessed_at)")
        print("   • Performance-Indizes für schnelle Suche")
        print("   • Full-Text Search (FTS5) für erweiterte Suchfunktionen")
        print("   • Automatische FTS-Updates über Trigger")
        print("\n🎯 Das DMS ist jetzt einsatzbereit!")
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        if 'conn' in locals():
            conn.close()
        raise


if __name__ == "__main__":
    asyncio.run(run_sqlite_migration()) 