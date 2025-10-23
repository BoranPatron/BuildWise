#!/usr/bin/env python3
"""
PostgreSQL Schema Check for deployed Version
Checks the current schema of the users table
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def check_postgresql_schema():
    """Checks the current schema of the PostgreSQL users table"""
    
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
            # Check if users table exists
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'users' not in tables:
                print("ERROR: users table does not exist!")
                return False
            
            print("OK: users table exists")
            
            # Get all columns
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            print(f"[INFO] users table has {len(column_names)} columns:")
            for i, col in enumerate(columns, 1):
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  {i:2d}. {col['name']:<25} {col['type']} {nullable}")
            
            # Check for hashed_password specifically
            if 'hashed_password' in column_names:
                print("\nOK: hashed_password column EXISTS")
                return True
            else:
                print("\nERROR: hashed_password column MISSING")
                return False
                
    except Exception as e:
        print(f"ERROR: Error checking PostgreSQL schema: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    print("PostgreSQL Schema Check for deployed Version")
    print("=" * 50)
    
    has_hashed_password = check_postgresql_schema()
    
    if has_hashed_password:
        print("\nOK: Schema is correct - hashed_password column exists!")
        print("The OAuth Microsoft login should work.")
    else:
        print("\nERROR: Schema is missing hashed_password column!")
        print("Run fix_postgresql_schema.py to fix this issue.")
        sys.exit(1)



