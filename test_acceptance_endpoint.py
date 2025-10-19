#!/usr/bin/env python3
import asyncio
import httpx
import json

async def test_acceptance_endpoint():
    """Test the acceptance milestone endpoint directly"""
    base_url = "http://localhost:8000/api/v1"
    
    # Login first
    login_data = {
        "username": "test@buildwise.local",
        "password": "test123"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Login
            print("Attempting login...")
            login_response = await client.post(f"{base_url}/auth/login", data=login_data)
            print(f"Login status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get("access_token")
                print(f"Token received: {token[:50]}..." if token else "No token")
                
                if token:
                    # Test acceptance milestone endpoint
                    headers = {"Authorization": f"Bearer {token}"}
                    print("Testing acceptance milestone endpoint...")
                    
                    # Test with milestone ID 1
                    acceptance_response = await client.get(
                        f"{base_url}/acceptance/milestone/1",
                        headers=headers
                    )
                    
                    print(f"Acceptance status: {acceptance_response.status_code}")
                    print(f"Acceptance response: {acceptance_response.text}")
                    
                    if acceptance_response.status_code != 200:
                        print(f"Error details: {acceptance_response.text}")
                else:
                    print("No token received from login")
            else:
                print(f"Login failed: {login_response.text}")
                
        except Exception as e:
            print(f"Error testing endpoint: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_acceptance_endpoint())

