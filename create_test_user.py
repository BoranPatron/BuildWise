#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.core.security import get_password_hash

async def create_test_user():
    try:
        async with engine.begin() as conn:
            # Create a test user
            password_hash = get_password_hash("test123")
            
            result = await conn.execute(text("""
                INSERT OR REPLACE INTO users 
                (email, hashed_password, first_name, last_name, user_type, user_role, auth_provider, status, is_active, data_processing_consent, privacy_policy_accepted, terms_accepted)
                VALUES 
                ('test@buildwise.local', :password_hash, 'Test', 'User', 'PRIVATE', 'BAUTRAEGER', 'email', 'active', 1, 1, 1, 1)
            """), {"password_hash": password_hash})
            
            print(f"Created test user with password 'test123'")
            
    except Exception as e:
        print(f"Error creating test user: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user())
