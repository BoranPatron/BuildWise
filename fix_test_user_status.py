#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def fix_test_user_status():
    try:
        async with engine.begin() as conn:
            # Update test user status to uppercase
            result = await conn.execute(text("""
                UPDATE users 
                SET status = 'ACTIVE' 
                WHERE email = 'test@buildwise.local'
            """))
            
            print(f"Updated {result.rowcount} test user(s)")
            
    except Exception as e:
        print(f"Error fixing test user status: {e}")

if __name__ == "__main__":
    asyncio.run(fix_test_user_status())

