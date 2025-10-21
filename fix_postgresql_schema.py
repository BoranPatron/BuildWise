#!/usr/bin/env python3
"""
PostgreSQL Schema Fix für deployed Version
Fügt die fehlende hashed_password Spalte zur users Tabelle hinzu
"""

import os
import sys
from pathlib import Path

# Füge das app-Verzeichnis zum Python-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def fix_postgresql_schema():
    """Fügt die fehlende hashed_password Spalte zur PostgreSQL users Tabelle hinzu"""
    
    # Get database URL from environment or config
    database_url = os.getenv("DATABASE_URL", str(settings.database_url))
    
    # Convert async URLs to sync
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    # Add SSL for PostgreSQL if needed
    if database_url.startswith("postgresql") and "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"
    
    print(f"[INFO] Connecting to PostgreSQL database...")
    print(f"[INFO] Database URL: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    
    try:
        # Create engine with proper SSL settings for PostgreSQL
        connect_args = {
            "sslmode": "require",
            "connect_timeout": 30
        }
        
        engine = create_engine(database_url, connect_args=connect_args)
        
        with engine.connect() as conn:
            # Check if hashed_password column exists
            inspector = inspect(engine)
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            print(f"[INFO] Current users table columns: {len(column_names)}")
            print(f"[INFO] Columns: {', '.join(column_names[:10])}{'...' if len(column_names) > 10 else ''}")
            
            if 'hashed_password' in column_names:
                print("✅ hashed_password column already exists!")
                return True
            
            print("❌ hashed_password column missing - adding it...")
            
            # Add the missing hashed_password column
            alter_sql = """
            ALTER TABLE users 
            ADD COLUMN hashed_password VARCHAR NULL;
            """
            
            print(f"[INFO] Executing: {alter_sql.strip()}")
            conn.execute(text(alter_sql))
            conn.commit()
            
            print("✅ hashed_password column added successfully!")
            
            # Verify the column was added
            inspector = inspect(engine)
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            if 'hashed_password' in column_names:
                print("✅ Verification successful: hashed_password column now exists!")
                return True
            else:
                print("❌ Verification failed: hashed_password column still missing!")
                return False
                
    except Exception as e:
        print(f"❌ Error fixing PostgreSQL schema: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    print("🔧 PostgreSQL Schema Fix für deployed Version")
    print("=" * 50)
    
    success = fix_postgresql_schema()
    
    if success:
        print("\n✅ Schema fix completed successfully!")
        print("The OAuth Microsoft login should now work.")
    else:
        print("\n❌ Schema fix failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)