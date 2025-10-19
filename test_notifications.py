#!/usr/bin/env python3
import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine, get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService

async def test_notifications():
    try:
        # Get a test user
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT id, email FROM users LIMIT 1"))
            user_data = result.fetchone()
            
        if not user_data:
            print("No users found in database")
            return
            
        user_id = user_data[0]
        print(f"Testing with user ID: {user_id}")
        
        # Test notification service
        async for db in get_db():
            try:
                notifications = await NotificationService.get_user_notifications(
                    db=db,
                    user_id=user_id,
                    limit=10,
                    offset=0,
                    unread_only=False,
                    unacknowledged_only=True
                )
                print(f"Found {len(notifications)} notifications")
                
                for notification in notifications:
                    print(f"- {notification.title}: {notification.message[:50]}...")
                    
            except Exception as e:
                print(f"Error in notification service: {e}")
                import traceback
                traceback.print_exc()
            break
            
    except Exception as e:
        print(f"Error testing notifications: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_notifications())

