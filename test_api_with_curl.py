#!/usr/bin/env python3
import subprocess
import json

def test_projects_api_with_curl():
    print("🔍 Test: Projects API mit cURL")
    print("=" * 40)
    
    # Test ohne Authentication (sollte 401 geben)
    print("\n1. Test ohne Token (sollte 401 geben):")
    try:
        result = subprocess.run([
            'curl', '-s', '-w', '\\nHTTP_CODE:%{http_code}\\n',
            'http://localhost:8000/api/v1/projects/'
        ], capture_output=True, text=True, timeout=10)
        
        print(f"Response: {result.stdout}")
        print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. API Docs Test:")
    try:
        result = subprocess.run([
            'curl', '-s', '-w', '\\nHTTP_CODE:%{http_code}\\n',
            'http://localhost:8000/docs'
        ], capture_output=True, text=True, timeout=10)
        
        if "HTTP_CODE:200" in result.stdout:
            print("✅ Backend läuft korrekt")
        else:
            print("❌ Backend Problem")
            print(f"Response: {result.stdout[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n🔧 Für echten Test mit Token:")
    print("1. Im Frontend einloggen als Dienstleister")
    print("2. F12 → Application → Local Storage → token kopieren")
    print("3. Dann ausführen:")
    print('   curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/projects/')

if __name__ == "__main__":
    test_projects_api_with_curl()