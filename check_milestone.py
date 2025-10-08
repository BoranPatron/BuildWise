#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_milestone():
    try:
        async with engine.begin() as conn:
            # Check if milestone 1 exists
            result = await conn.execute(text("SELECT id, title, project_id FROM milestones WHERE id = 1"))
            milestone = result.fetchone()
            
            if milestone:
                print(f"Milestone 1 found: ID={milestone[0]}, Title={milestone[1]}, Project={milestone[2]}")
            else:
                print("Milestone 1 not found")
                
            # Check if there are any milestones
            result = await conn.execute(text("SELECT COUNT(*) FROM milestones"))
            count = result.scalar()
            print(f"Total milestones in database: {count}")
            
            # List first few milestones
            result = await conn.execute(text("SELECT id, title FROM milestones LIMIT 5"))
            milestones = result.fetchall()
            print("First few milestones:")
            for m in milestones:
                print(f"- ID: {m[0]}, Title: {m[1]}")
                
    except Exception as e:
        print(f"Error checking milestone: {e}")

if __name__ == "__main__":
    asyncio.run(check_milestone())

