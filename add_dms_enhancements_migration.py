#!/usr/bin/env python3
"""
Migration: DMS Enhancements
Fügt neue Felder und Enums für das erweiterte Dokumentenmanagementsystem hinzu
"""

import asyncio
import sys
import os

# Pfad zum Projektverzeichnis hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine


async def run_migration():
    """Führt die DMS Enhancement Migration aus"""
    
    migration_sql = """
    -- Neue Enums hinzufügen
    DO $$ BEGIN
        CREATE TYPE documentstatus AS ENUM ('draft', 'review', 'approved', 'rejected', 'archived');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    DO $$ BEGIN
        CREATE TYPE documentcategory AS ENUM ('planning', 'contracts', 'finance', 'execution', 'documentation');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    -- DocumentType Enum erweitern
    DO $$ BEGIN
        ALTER TYPE documenttype ADD VALUE 'blueprint';
        ALTER TYPE documenttype ADD VALUE 'certificate';
        ALTER TYPE documenttype ADD VALUE 'report';
        ALTER TYPE documenttype ADD VALUE 'video';
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    -- Neue Spalten hinzufügen
    ALTER TABLE documents 
    ADD COLUMN IF NOT EXISTS subcategory VARCHAR,
    ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS status documentstatus DEFAULT 'draft',
    ADD COLUMN IF NOT EXISTS accessed_at TIMESTAMP WITH TIME ZONE;
    
    -- Category Spalte von VARCHAR zu ENUM ändern
    DO $$ BEGIN
        -- Temporäre Spalte erstellen
        ALTER TABLE documents ADD COLUMN IF NOT EXISTS category_new documentcategory DEFAULT 'documentation';
        
        -- Bestehende Werte migrieren
        UPDATE documents SET category_new = 
            CASE 
                WHEN category = 'planning' THEN 'planning'::documentcategory
                WHEN category = 'contracts' THEN 'contracts'::documentcategory
                WHEN category = 'finance' THEN 'finance'::documentcategory
                WHEN category = 'execution' THEN 'execution'::documentcategory
                WHEN category = 'documentation' THEN 'documentation'::documentcategory
                ELSE 'documentation'::documentcategory
            END;
        
        -- Alte Spalte löschen und neue umbenennen
        ALTER TABLE documents DROP COLUMN IF EXISTS category;
        ALTER TABLE documents RENAME COLUMN category_new TO category;
    EXCEPTION
        WHEN others THEN 
            -- Falls die Spalte bereits existiert oder ein anderer Fehler auftritt
            null;
    END $$;
    
    -- Indizes für bessere Performance
    CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
    CREATE INDEX IF NOT EXISTS idx_documents_subcategory ON documents(subcategory);
    CREATE INDEX IF NOT EXISTS idx_documents_is_favorite ON documents(is_favorite);
    CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
    CREATE INDEX IF NOT EXISTS idx_documents_accessed_at ON documents(accessed_at);
    
    -- Volltextsuche Index für bessere Suchperformance
    CREATE INDEX IF NOT EXISTS idx_documents_fulltext ON documents USING gin(
        to_tsvector('german', title || ' ' || COALESCE(description, '') || ' ' || COALESCE(tags, ''))
    );
    
    COMMIT;
    """
    
    async with engine.begin() as conn:
        try:
            print("🚀 Starte DMS Enhancement Migration...")
            
            # Migration ausführen
            await conn.execute(text(migration_sql))
            
            print("✅ DMS Enhancement Migration erfolgreich abgeschlossen!")
            print("\n📋 Hinzugefügte Features:")
            print("   • Erweiterte Dokumentenkategorien (planning, contracts, finance, execution, documentation)")
            print("   • Unterkategorien für flexible Organisation")
            print("   • Favoriten-System für wichtige Dokumente")
            print("   • Status-Tracking (draft, review, approved, rejected, archived)")
            print("   • Zugriffs-Tracking (accessed_at)")
            print("   • Erweiterte Dokumenttypen (blueprint, certificate, report, video)")
            print("   • Performance-Indizes für schnelle Suche")
            print("   • Volltextsuche mit deutscher Sprache")
            
        except Exception as e:
            print(f"❌ Fehler bei der Migration: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_migration()) 