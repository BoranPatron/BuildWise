#!/usr/bin/env python3
"""
Überprüft das Datenbankschema der Projekte-Tabelle
"""

import asyncio
import sys
import os

# Pfad zum app-Verzeichnis hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from sqlalchemy import inspect

async def check_project_schema():
    """Überprüft das Datenbankschema der Projekte-Tabelle"""
    
    print("🗄️ Überprüfe Projekte-Tabelle Schema")
    print("=" * 50)
    
    async for db in get_db():
        try:
            # Verwende run_sync für die Inspektion
            def inspect_schema(conn):
                inspector = inspect(conn)
                if 'projects' in inspector.get_table_names():
                    columns = inspector.get_columns('projects')
                    return columns
                return []
            
            columns = await db.run_sync(inspect_schema)
            
            if columns:
                print(f"📋 Projekte-Tabelle hat {len(columns)} Spalten:")
                print()
                
                for col in columns:
                    print(f"  {col['name']}: {col['type']}")
                    if col.get('nullable') is not None:
                        print(f"    Nullable: {col['nullable']}")
                    if col.get('default') is not None:
                        print(f"    Default: {col['default']}")
                    print()
                
                # Überprüfe spezifisch nach address-bezogenen Spalten
                address_columns = [col['name'] for col in columns if 'address' in col['name'].lower()]
                if address_columns:
                    print(f"📍 Address-bezogene Spalten gefunden: {address_columns}")
                else:
                    print("❌ Keine address-bezogenen Spalten gefunden")
                    
            else:
                print("❌ Projekte-Tabelle nicht gefunden")
                
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()
        
        break

if __name__ == "__main__":
    asyncio.run(check_project_schema()) 