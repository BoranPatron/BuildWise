#!/usr/bin/env python3
"""
Test-Skript für die Enum-Korrekturen
Testet die API-Endpunkte nach der Korrektur
"""
import requests
import json
import os
from datetime import datetime


def test_milestone_progress_api():
    """Testet die Milestone Progress API"""
    
    # Render API URL
    base_url = "https://buildwise-api.onrender.com"
    
    print(f"[INFO] Testing Milestone Progress API at {base_url}")
    print(f"[INFO] Test started at {datetime.now()}")
    
    # Test 1: GET /api/v1/milestones/1/progress/
    print("\n[TEST 1] GET /api/v1/milestones/1/progress/")
    try:
        response = requests.get(f"{base_url}/api/v1/milestones/1/progress/")
        print(f"[RESULT] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] API call successful! Found {len(data)} progress updates")
            if data:
                print(f"[INFO] First update: {data[0].get('message', 'No message')[:50]}...")
        elif response.status_code == 500:
            print(f"[ERROR] Server error: {response.text}")
        else:
            print(f"[INFO] Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
    
    # Test 2: Health Check
    print("\n[TEST 2] Health Check")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"[RESULT] Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"[SUCCESS] Health check passed: {response.json()}")
        else:
            print(f"[ERROR] Health check failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
    
    # Test 3: API Docs
    print("\n[TEST 3] API Documentation")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"[RESULT] Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"[SUCCESS] API docs accessible")
        else:
            print(f"[ERROR] API docs not accessible: {response.text}")
    except Exception as e:
        print(f"[ERROR] API docs check failed: {e}")
    
    print(f"\n[INFO] Test completed at {datetime.now()}")


if __name__ == "__main__":
    test_milestone_progress_api()
