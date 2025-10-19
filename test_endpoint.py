#!/usr/bin/env python3
import asyncio
import httpx
import json

async def test_notifications_endpoint():
    """Test the notifications endpoint directly"""
    base_url = "http://localhost:8000/api/v1"
    
    # First, let's try to get a token by logging in
    login_data = {
        "username": "admin@buildwise.local",
        "password": "admin123"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Try to login
            print("Attempting login...")
            login_response = await client.post(f"{base_url}/auth/login", data=login_data)
            print(f"Login status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get("access_token")
                print(f"Token received: {token[:50]}..." if token else "No token")
                
                if token:
                    # Test notifications endpoint
                    headers = {"Authorization": f"Bearer {token}"}
                    print("Testing notifications endpoint...")
                    
                    notifications_response = await client.get(
                        f"{base_url}/notifications/",
                        headers=headers,
                        params={"limit": 20, "unacknowledged_only": True}
                    )
                    
                    print(f"Notifications status: {notifications_response.status_code}")
                    print(f"Notifications response: {notifications_response.text}")
                    
                    if notifications_response.status_code != 200:
                        print(f"Error details: {notifications_response.text}")
                else:
                    print("No token received from login")
            else:
                print(f"Login failed: {login_response.text}")
                
        except Exception as e:
            print(f"Error testing endpoint: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_notifications_endpoint())
