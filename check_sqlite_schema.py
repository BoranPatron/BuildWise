#!/usr/bin/env python3
"""
Simple SQLite Schema Check
Checks the current schema of the users table in SQLite database
"""

import sqlite3
import os
from pathlib import Path

def check_sqlite_schema():
    """Checks the current schema of the SQLite users table"""
    
    # Look for database files
    db_files = [
        "buildwise.db",
        "building_wise.db",
        "./buildwise.db"
    ]
    
    db_path = None
    for db_file in db_files:
        if os.path.exists(db_file):
            db_path = db_file
            break
    
    if not db_path:
        print("ERROR: No SQLite database file found!")
        return False
    
    print(f"[INFO] Found database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("ERROR: users table does not exist!")
            return False
        
        print("OK: users table exists")
        
        # Get all columns
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        
        print(f"[INFO] users table has {len(columns)} columns:")
        column_names = []
        for i, col in enumerate(columns, 1):
            col_name = col[1]
            col_type = col[2]
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            column_names.append(col_name)
            print(f"  {i:2d}. {col_name:<25} {col_type} {nullable}")
        
        # Check for hashed_password specifically
        if 'hashed_password' in column_names:
            print("\nOK: hashed_password column EXISTS")
            return True
        else:
            print("\nERROR: hashed_password column MISSING")
            return False
            
    except Exception as e:
        print(f"ERROR: Error checking SQLite schema: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("SQLite Schema Check")
    print("=" * 30)
    
    has_hashed_password = check_sqlite_schema()
    
    if has_hashed_password:
        print("\nOK: Schema is correct - hashed_password column exists!")
        print("The OAuth Microsoft login should work.")
    else:
        print("\nERROR: Schema is missing hashed_password column!")
        print("Need to add the missing column to fix OAuth login.")



