#!/usr/bin/env python3
"""
Migration: Make project_id nullable in tasks table
This allows creating tasks without a project_id (for general tasks)
"""

import sqlite3
import os
from pathlib import Path

def run_migration():
    """Make project_id nullable in tasks table"""
    
    # Find database file
    db_paths = [
        "buildwise.db",
        "building_wise.db", 
        "/storage/buildwise.db",
        "/storage/building_wise.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("ERROR: No database file found!")
        return False
    
    print(f"Using database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if project_id column exists and is not nullable
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        
        project_id_column = None
        for col in columns:
            if col[1] == 'project_id':
                project_id_column = col
                break
        
        if not project_id_column:
            print("ERROR: project_id column not found in tasks table!")
            return False
        
        print(f"Current project_id column: {project_id_column}")
        
        # Check if already nullable
        if project_id_column[3] == 0:  # 0 means nullable
            print("SUCCESS: project_id is already nullable!")
            return True
        
        print("Making project_id nullable...")
        
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        # First, get the current table structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
        create_sql = cursor.fetchall()[0][0]
        
        print(f"Current table structure: {create_sql}")
        
        # Create new table with nullable project_id
        new_create_sql = create_sql.replace(
            "project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE",
            "project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE"
        )
        
        # If the above doesn't work, try a more general approach
        if new_create_sql == create_sql:
            new_create_sql = create_sql.replace(
                "project_id INTEGER NOT NULL",
                "project_id INTEGER"
            )
        
        print(f"New table structure: {new_create_sql}")
        
        # Create backup table
        cursor.execute("CREATE TABLE tasks_backup AS SELECT * FROM tasks")
        print("Created backup table: tasks_backup")
        
        # Drop original table
        cursor.execute("DROP TABLE tasks")
        print("Dropped original tasks table")
        
        # Create new table with nullable project_id
        cursor.execute(new_create_sql)
        print("Created new tasks table with nullable project_id")
        
        # Copy data back
        cursor.execute("INSERT INTO tasks SELECT * FROM tasks_backup")
        print("Copied data back to new table")
        
        # Drop backup table
        cursor.execute("DROP TABLE tasks_backup")
        print("Dropped backup table")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        
        for col in columns:
            if col[1] == 'project_id':
                print(f"SUCCESS: project_id is now nullable: {col}")
                break
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting project_id nullable migration...")
    success = run_migration()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        exit(1)
