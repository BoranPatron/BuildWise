#!/usr/bin/env python3
import requests
import json

def test_projects_api():
    print("🔍 Test: Direct Projects API Call")
    print("=" * 40)
    
    # We need to simulate the API call with proper authentication
    # Since we can't get the JWT token easily, let's test the service directly
    
    import asyncio
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from app.database import get_async_session
    from app.services.project_service import get_projects_for_user
    
    async def test_service():
        async for db in get_async_session():
            print("🔄 Testing get_projects_for_user service directly...")
            
            # Test User 4 (Bauträger)
            user4_projects = await get_projects_for_user(db, 4)
            print(f"👤 User 4 (Bauträger): {len(user4_projects)} Projekte")
            for project in user4_projects:
                print(f"  - Projekt {project.id}: {project.name} (Owner: {project.owner_id})")
            
            # Test User 6 (Dienstleister) 
            user6_projects = await get_projects_for_user(db, 6)
            print(f"👤 User 6 (Dienstleister): {len(user6_projects)} Projekte")
            for project in user6_projects:
                print(f"  - Projekt {project.id}: {project.name} (Owner: {project.owner_id})")
            
            break
    
    asyncio.run(test_service())

if __name__ == "__main__":
    test_projects_api()