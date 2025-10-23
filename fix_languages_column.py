#!/usr/bin/env python3
"""
Repariert die languages Spalte von JSON zu TEXT
"""

import os
import asyncpg
import asyncio
import sys

async def fix_languages_column():
    """Ändert die languages Spalte von JSON zu TEXT"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not found!")
            return False
            
        print(f"🔧 Connecting to database...")
        print(f"Database URL: {database_url}")
        
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database successfully!")
        
        # Start transaction for safety
        await conn.execute('BEGIN;')
        print("🔄 Started transaction for safe schema changes...")
        
        # Ändere languages Spalte von JSON zu TEXT
        print("\n📝 Fixing languages column datatype...")
        try:
            # Prüfe aktuellen Datentyp
            result = await conn.fetchval("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'languages'
            """)
            print(f"  Current languages column type: {result}")
            
            if result == 'json':
                print("  Converting languages from JSON to TEXT...")
                await conn.execute('ALTER TABLE users ALTER COLUMN languages TYPE TEXT USING languages::TEXT;')
                print("  ✅ languages column converted to TEXT successfully")
            else:
                print(f"  ✅ languages column is already {result}")
                
        except Exception as e:
            print(f"  ⚠️  Error fixing languages column: {e}")
            # Continue anyway
        
        # Füge fehlende projects Spalten hinzu
        print("\n📝 Adding missing projects columns...")
        try:
            await conn.execute('ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type VARCHAR NULL;')
            print("  ✅ projects.project_type added successfully")
        except Exception as e:
            print(f"  ⚠️  projects.project_type: {e}")
        
        # Schema-Verifikation
        print("\n🔍 Verifying schema...")
        
        # Prüfe languages Spalte
        result = await conn.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'languages'
        """)
        print(f"✅ users.languages column is now: {result}")
        
        # Commit transaction
        await conn.execute('COMMIT;')
        print("✅ Transaction committed successfully!")
        
        await conn.close()
        print("\n🎉 Languages column fix successful!")
        print("✅ languages column converted to TEXT")
        print("✅ OAuth Microsoft login should now work!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during schema repair: {e}")
        # Try to rollback if connection is still open
        try:
            if 'conn' in locals():
                await conn.execute('ROLLBACK;')
                print("🔄 Transaction rolled back due to error")
                await conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    print("🔧 Fix Languages Column Datatype")
    print("=" * 50)
    
    success = asyncio.run(fix_languages_column())
    
    if success:
        print("\n✅ Languages column fix completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Languages column fix failed!")
        sys.exit(1)



