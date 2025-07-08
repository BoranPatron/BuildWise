#!/usr/bin/env python3
"""
Migration script to create cost_positions table
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.cost_position import CostPosition
from app.models.base import Base


async def create_cost_positions_table():
    """Create the cost_positions table"""
    try:
        async with engine.begin() as conn:
            # Create the table
            await conn.run_sync(Base.metadata.create_all, tables=[CostPosition.__table__])
            print("✅ Cost positions table created successfully")
            
    except Exception as e:
        print(f"❌ Error creating cost positions table: {e}")
        raise


async def main():
    """Main migration function"""
    print("🔄 Starting cost positions table migration...")
    
    try:
        await create_cost_positions_table()
        print("✅ Migration completed successfully")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 