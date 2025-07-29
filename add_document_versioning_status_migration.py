#!/usr/bin/env python3
"""
Migration: Dokumentenversionierung und Status-Logik nach Best Practices
Basiert auf: Semantic Versioning, Document Lifecycle Management, Audit Trail
"""

import sqlite3
import os
from datetime import datetime

def add_document_versioning_status():
    """Fügt Dokumentenversionierung und erweiterte Status-Logik hinzu"""
    
    print("🚀 Füge Dokumentenversionierung und Status-Logik hinzu...")
    
    # Verbinde zur Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        # 1. Erweitere documents Tabelle um Versionierung
        print("\n📋 Erweitere documents Tabelle...")
        
        # Prüfe ob Spalten bereits existieren
        cursor.execute("PRAGMA table_info(documents)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ('version_number', 'VARCHAR(50) DEFAULT "1.0.0"'),
            ('version_major', 'INTEGER DEFAULT 1'),
            ('version_minor', 'INTEGER DEFAULT 0'),
            ('version_patch', 'INTEGER DEFAULT 0'),
            ('is_latest_version', 'BOOLEAN DEFAULT TRUE'),
            ('parent_document_id', 'INTEGER'),
            ('document_status', 'VARCHAR(50) DEFAULT "DRAFT"'),
            ('workflow_stage', 'VARCHAR(50) DEFAULT "CREATED"'),
            ('approval_status', 'VARCHAR(50) DEFAULT "PENDING"'),
            ('review_status', 'VARCHAR(50) DEFAULT "NOT_REVIEWED"'),
            ('locked_by', 'INTEGER'),
            ('locked_at', 'DATETIME'),
            ('approved_by', 'INTEGER'),
            ('approved_at', 'DATETIME'),
            ('rejected_by', 'INTEGER'),
            ('rejected_at', 'DATETIME'),
            ('rejection_reason', 'TEXT'),
            ('expires_at', 'DATETIME'),
            ('archived_at', 'DATETIME'),
            ('checksum', 'VARCHAR(255)'),
            ('file_format_version', 'VARCHAR(50)'),
            ('metadata_json', 'TEXT'),
            ('access_level', 'VARCHAR(50) DEFAULT "INTERNAL"'),
            ('sharing_permissions', 'TEXT'),
            ('download_count', 'INTEGER DEFAULT 0'),
            ('last_accessed_by', 'INTEGER'),
            ('last_accessed_at', 'DATETIME')
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE documents ADD COLUMN {column_name} {column_def}")
                print(f"  ✅ Spalte hinzugefügt: {column_name}")
        
        # 2. Erstelle document_versions Tabelle für Versionsverlauf
        print("\n📋 Erstelle document_versions Tabelle...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                version_number VARCHAR(50) NOT NULL,
                version_major INTEGER NOT NULL,
                version_minor INTEGER NOT NULL,
                version_patch INTEGER NOT NULL,
                file_path VARCHAR(500),
                file_name VARCHAR(255),
                file_size INTEGER,
                mime_type VARCHAR(100),
                checksum VARCHAR(255),
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                change_description TEXT,
                change_type VARCHAR(50) DEFAULT "MINOR",
                is_active BOOLEAN DEFAULT TRUE,
                metadata_json TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                UNIQUE(document_id, version_number)
            )
        """)
        print("  ✅ document_versions Tabelle erstellt")
        
        # 3. Erstelle document_status_history Tabelle für Audit Trail
        print("\n📋 Erstelle document_status_history Tabelle...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                version_number VARCHAR(50),
                old_status VARCHAR(50),
                new_status VARCHAR(50),
                old_workflow_stage VARCHAR(50),
                new_workflow_stage VARCHAR(50),
                changed_by INTEGER,
                changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                change_reason TEXT,
                metadata_json TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (changed_by) REFERENCES users(id)
            )
        """)
        print("  ✅ document_status_history Tabelle erstellt")
        
        # 4. Erstelle document_shares Tabelle für Dokument-Sharing
        print("\n📋 Erstelle document_shares Tabelle...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                shared_with_user_id INTEGER,
                shared_with_project_id INTEGER,
                shared_with_trade_id INTEGER,
                share_type VARCHAR(50) NOT NULL DEFAULT "READ_ONLY",
                permissions TEXT,
                shared_by INTEGER NOT NULL,
                shared_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                access_count INTEGER DEFAULT 0,
                last_accessed_at DATETIME,
                is_active BOOLEAN DEFAULT TRUE,
                metadata_json TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (shared_with_user_id) REFERENCES users(id),
                FOREIGN KEY (shared_with_project_id) REFERENCES projects(id),
                FOREIGN KEY (shared_by) REFERENCES users(id)
            )
        """)
        print("  ✅ document_shares Tabelle erstellt")
        
        # 5. Erstelle document_access_log Tabelle für Zugriffs-Tracking
        print("\n📋 Erstelle document_access_log Tabelle...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                version_number VARCHAR(50),
                user_id INTEGER,
                access_type VARCHAR(50) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                duration_seconds INTEGER,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                metadata_json TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("  ✅ document_access_log Tabelle erstellt")
        
        # 6. Erstelle Indizes für Performance
        print("\n📋 Erstelle Indizes...")
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_documents_version ON documents(version_number, is_latest_version)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(document_status, workflow_stage)",
            "CREATE INDEX IF NOT EXISTS idx_documents_parent ON documents(parent_document_id)",
            "CREATE INDEX IF NOT EXISTS idx_document_versions_doc ON document_versions(document_id, version_number)",
            "CREATE INDEX IF NOT EXISTS idx_document_status_history_doc ON document_status_history(document_id, changed_at)",
            "CREATE INDEX IF NOT EXISTS idx_document_shares_doc ON document_shares(document_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_document_shares_user ON document_shares(shared_with_user_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_document_access_log_doc ON document_access_log(document_id, accessed_at)"
        ]
        
        for index_sql in indices:
            cursor.execute(index_sql)
        print("  ✅ Indizes erstellt")
        
        # 7. Migriere bestehende Dokumente
        print("\n📋 Migriere bestehende Dokumente...")
        cursor.execute("SELECT id, title, file_path, file_name, file_size, mime_type, created_at, uploaded_by FROM documents")
        existing_docs = cursor.fetchall()
        
        for doc_id, title, file_path, file_name, file_size, mime_type, created_at, uploaded_by in existing_docs:
            # Erstelle Versionseintrag für bestehende Dokumente
            cursor.execute("""
                INSERT OR IGNORE INTO document_versions (
                    document_id, version_number, version_major, version_minor, version_patch,
                    file_path, file_name, file_size, mime_type, created_by, created_at,
                    change_description, change_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, "1.0.0", 1, 0, 0,
                file_path, file_name, file_size, mime_type, uploaded_by, created_at,
                "Initial version", "MAJOR"
            ))
            
            # Erstelle Status-History für bestehende Dokumente
            cursor.execute("""
                INSERT OR IGNORE INTO document_status_history (
                    document_id, version_number, old_status, new_status,
                    old_workflow_stage, new_workflow_stage, changed_by, changed_at,
                    change_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, "1.0.0", None, "PUBLISHED",
                None, "COMPLETED", uploaded_by, created_at,
                "Document migration - initial status"
            ))
        
        print(f"  ✅ {len(existing_docs)} bestehende Dokumente migriert")
        
        # 8. Aktualisiere bestehende Dokumente mit Standard-Werten
        cursor.execute("""
            UPDATE documents 
            SET document_status = 'PUBLISHED',
                workflow_stage = 'COMPLETED',
                approval_status = 'APPROVED',
                review_status = 'APPROVED'
            WHERE document_status IS NULL OR document_status = ''
        """)
        
        # Commit Änderungen
        conn.commit()
        
        # 9. Zeige Zusammenfassung
        print(f"\n📊 Migration erfolgreich!")
        
        # Zeige neue Tabellen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'document%'")
        tables = cursor.fetchall()
        print(f"\n📋 Dokument-Tabellen:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} Einträge")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Fehler bei Migration: {e}")
        raise
    finally:
        conn.close()

def create_document_enums():
    """Definiert die Enums für Dokumentenstatus"""
    
    enums = {
        'DOCUMENT_STATUS': [
            'DRAFT',           # Entwurf
            'IN_REVIEW',       # In Prüfung
            'APPROVED',        # Genehmigt
            'REJECTED',        # Abgelehnt
            'PUBLISHED',       # Veröffentlicht
            'ARCHIVED',        # Archiviert
            'DELETED'          # Gelöscht
        ],
        'WORKFLOW_STAGE': [
            'CREATED',         # Erstellt
            'UPLOADED',        # Hochgeladen
            'CATEGORIZED',     # Kategorisiert
            'REVIEWED',        # Geprüft
            'APPROVED',        # Genehmigt
            'PUBLISHED',       # Veröffentlicht
            'SHARED',          # Geteilt
            'COMPLETED',       # Abgeschlossen
            'ARCHIVED'         # Archiviert
        ],
        'APPROVAL_STATUS': [
            'PENDING',         # Ausstehend
            'IN_REVIEW',       # In Prüfung
            'APPROVED',        # Genehmigt
            'REJECTED',        # Abgelehnt
            'REQUIRES_CHANGES' # Änderungen erforderlich
        ],
        'REVIEW_STATUS': [
            'NOT_REVIEWED',    # Nicht geprüft
            'IN_REVIEW',       # In Prüfung
            'REVIEWED',        # Geprüft
            'APPROVED',        # Genehmigt
            'REJECTED'         # Abgelehnt
        ],
        'SHARE_TYPE': [
            'READ_ONLY',       # Nur lesen
            'DOWNLOAD',        # Herunterladen
            'COMMENT',         # Kommentieren
            'EDIT',            # Bearbeiten
            'FULL_ACCESS'      # Vollzugriff
        ],
        'ACCESS_LEVEL': [
            'PUBLIC',          # Öffentlich
            'INTERNAL',        # Intern
            'CONFIDENTIAL',    # Vertraulich
            'RESTRICTED'       # Eingeschränkt
        ],
        'CHANGE_TYPE': [
            'MAJOR',           # Hauptversion (Breaking Changes)
            'MINOR',           # Nebenversion (Neue Features)
            'PATCH',           # Patch (Bugfixes)
            'HOTFIX'           # Hotfix (Kritische Fixes)
        ]
    }
    
    print("\n📋 Definierte Enums:")
    for enum_name, values in enums.items():
        print(f"  - {enum_name}: {', '.join(values)}")
    
    return enums

if __name__ == "__main__":
    print("🚀 Starte Dokumentenversionierung und Status-Migration...")
    
    # Definiere Enums
    enums = create_document_enums()
    
    # Führe Migration aus
    add_document_versioning_status()
    
    print(f"\n✅ Migration vollständig abgeschlossen!")
    print(f"\n🎯 Neue Features:")
    print(f"  - ✅ Semantische Versionierung (Major.Minor.Patch)")
    print(f"  - ✅ Dokument-Lifecycle-Management")
    print(f"  - ✅ Audit Trail für alle Änderungen")
    print(f"  - ✅ Dokument-Sharing-System")
    print(f"  - ✅ Zugriffs-Logging")
    print(f"  - ✅ Erweiterte Status-Workflows")
    print(f"  - ✅ Berechtigungsmanagement")
    
    print(f"\n📋 Nächste Schritte:")
    print(f"  1. Backend APIs für Versionierung erweitern")
    print(f"  2. Frontend für neue Features anpassen")
    print(f"  3. Bauträger Drag&Drop implementieren")
    print(f"  4. Dokument-Sharing-UI erstellen")