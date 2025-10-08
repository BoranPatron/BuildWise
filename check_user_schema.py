#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_user_schema():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = result.fetchall()
            print('Users table columns:')
            for col in columns:
                print(f"- {col[1]} ({col[2]}) - Nullable: {not col[3]}")
                
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    asyncio.run(check_user_schema())

