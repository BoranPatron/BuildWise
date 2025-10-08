#!/usr/bin/env python3
"""
Check if UserCredits table exists in the database
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from sqlalchemy import text

async def check_database():
    """Check if UserCredits table exists"""
    print("=== Checking Database ===")
    
    try:
        async for db in get_db():
            # Check if user_credits table exists
            result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_credits'"))
            tables = result.fetchall()
            
            if tables:
                print("[OK] user_credits table exists")
                
                # Check table structure
                result = await db.execute(text("PRAGMA table_info(user_credits)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                print(f"[INFO] user_credits table has {len(columns)} columns:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                # Check for missing columns
                required_columns = ['last_daily_deduction']
                missing_columns = [col for col in required_columns if col not in column_names]
                if missing_columns:
                    print(f"[WARNING] Missing columns: {missing_columns}")
                else:
                    print("[OK] All required columns present")
                    
            else:
                print("[ERROR] user_credits table does not exist!")
                
                # List all tables
                result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                all_tables = result.fetchall()
                print(f"[INFO] Available tables: {[t[0] for t in all_tables]}")
            
            break
            
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(check_database())
    if not success:
        sys.exit(1)
