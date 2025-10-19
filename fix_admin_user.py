#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def fix_admin_user_type():
    try:
        async with engine.begin() as conn:
            # Update admin user type from 'developer' to 'PROFESSIONAL'
            result = await conn.execute(text("""
                UPDATE users 
                SET user_type = 'PROFESSIONAL' 
                WHERE email = 'admin@buildwise.local'
            """))
            
            print(f"Updated {result.rowcount} admin user(s)")
            
            # Verify the change
            result = await conn.execute(text("""
                SELECT id, email, user_type FROM users 
                WHERE email = 'admin@buildwise.local'
            """))
            user = result.fetchone()
            
            if user:
                print(f"Admin user updated: ID={user[0]}, Email={user[1]}, Type={user[2]}")
            else:
                print("Admin user not found")
                
    except Exception as e:
        print(f"Error fixing admin user type: {e}")

if __name__ == "__main__":
    asyncio.run(fix_admin_user_type())

