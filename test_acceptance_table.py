#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def test_acceptance_table():
    try:
        async with engine.begin() as conn:
            # Check if acceptance table exists and has data
            result = await conn.execute(text("SELECT COUNT(*) FROM acceptances"))
            count = result.scalar()
            print(f"Total acceptances in database: {count}")
            
            # Check if there are any acceptances for milestone 1
            result = await conn.execute(text("SELECT COUNT(*) FROM acceptances WHERE milestone_id = 1"))
            count = result.scalar()
            print(f"Acceptances for milestone 1: {count}")
            
            # List all acceptances
            result = await conn.execute(text("SELECT id, milestone_id, project_id, contractor_id FROM acceptances LIMIT 5"))
            acceptances = result.fetchall()
            print("First few acceptances:")
            for a in acceptances:
                print(f"- ID: {a[0]}, Milestone: {a[1]}, Project: {a[2]}, Contractor: {a[3]}")
                
    except Exception as e:
        print(f"Error checking acceptance table: {e}")

if __name__ == "__main__":
    asyncio.run(test_acceptance_table())

