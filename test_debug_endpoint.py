#!/usr/bin/env python3
"""
Test-Skript für den Debug-Endpoint
"""

import requests
import json

def test_debug_endpoint():
    """Testet den Debug-Endpoint"""
    print("🧪 Teste Debug-Endpoint...")
    
    # Backend-URL
    base_url = "http://localhost:8000"
    endpoint = "/api/v1/milestones/debug/delete-all-milestones-and-quotes"
    
    # Test-Token (Admin-Token)
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBidWlsZHdpc2UuZGUiLCJleHAiOjE3NTI5NDY2OTh9.QybsYBe-4RUGdICzDAplsIzxmuaDGHTLMp5_k3YfKNA",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🌐 Teste Endpoint: {base_url}{endpoint}")
        
        # DELETE Request
        response = requests.delete(f"{base_url}{endpoint}", headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Erfolg!")
            print(f"📄 Response: {response.json()}")
        else:
            print("❌ Fehler!")
            print(f"📄 Response: {response.text}")
            
            # Versuche JSON zu parsen
            try:
                error_data = response.json()
                print(f"🔍 Error Detail: {error_data.get('detail', 'Kein Detail')}")
            except:
                print("📄 Raw Response:", response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ Backend nicht erreichbar (localhost:8000)")
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")

if __name__ == "__main__":
    test_debug_endpoint() 