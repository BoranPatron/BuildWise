#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.core.database import get_db
from app.api.milestones import get_all_active_milestones

async def test_milestone_endpoint():
    try:
        async for db in get_db():
            print('🔍 Testing get_all_active_milestones...')
            result = await get_all_active_milestones(db)
            print(f'✅ Success: {len(result)} milestones found')
            for i, m in enumerate(result[:3]):
                print(f'  - {m.get("id")}: {m.get("title")}')
            break
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_milestone_endpoint())
