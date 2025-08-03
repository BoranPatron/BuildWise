#!/usr/bin/env python3
"""
Direkter Test der Backend-Funktionen ohne HTTP-Layer
"""
import sys
import os
import asyncio
import sqlite3

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_backend_functions():
    print("🔍 Direct Backend Test")
    print("=" * 40)
    
    # Test 1: Direct Database Query
    print("\n1. DIRECT DATABASE TEST:")
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Check projects
    cursor.execute('SELECT id, name, owner_id FROM projects')
    projects = cursor.fetchall()
    print(f"📋 Projekte in DB: {len(projects)}")
    for project in projects:
        print(f"  - Projekt {project[0]}: {project[1]} (Owner: {project[2]})")
    
    # Check users
    cursor.execute('SELECT id, first_name, user_type FROM users WHERE id IN (4, 6)')
    users = cursor.fetchall()
    print(f"\n👥 Test-Users:")
    for user in users:
        print(f"  - User {user[0]}: {user[1]} ({user[2]})")
    
    conn.close()
    
    # Test 2: Backend Service Test
    print("\n2. BACKEND SERVICE TEST:")
    try:
        # Import backend modules
        from app.core.database import get_async_session
        from app.services.project_service import get_projects_for_user
        
        print("✅ Backend modules imported successfully")
        
        # Test the service function
        async for db in get_async_session():
            print("✅ Database session created")
            
            # Test User 4 (Bauträger)
            print("\n🔍 Testing User 4 (Bauträger):")
            user4_projects = await get_projects_for_user(db, 4)
            print(f"  Result: {len(user4_projects)} projects")
            for project in user4_projects:
                print(f"    - {project.id}: {project.name}")
            
            # Test User 6 (Dienstleister)
            print("\n🔍 Testing User 6 (Dienstleister):")
            user6_projects = await get_projects_for_user(db, 6)
            print(f"  Result: {len(user6_projects)} projects")
            for project in user6_projects:
                print(f"    - {project.id}: {project.name}")
            
            break
            
    except Exception as e:
        print(f"❌ Backend service test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    # Test 3: User Type Logic Test
    print("\n3. USER TYPE LOGIC TEST:")
    print("Testing the logic in get_projects_for_user...")
    
    try:
        from app.models import User
        from sqlalchemy import select
        
        async for db in get_async_session():
            # Get user 6 details
            user_result = await db.execute(select(User).where(User.id == 6))
            user = user_result.scalars().first()
            
            if user:
                print(f"User 6 details:")
                print(f"  - user_type: '{user.user_type}'")
                print(f"  - Logic check: user_type == 'SERVICE_PROVIDER' -> {user.user_type == 'SERVICE_PROVIDER'}")
                print(f"  - Should see all projects: {user.user_type == 'SERVICE_PROVIDER'}")
            else:
                print("❌ User 6 not found")
            
            break
            
    except Exception as e:
        print(f"❌ User type logic test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend_functions())