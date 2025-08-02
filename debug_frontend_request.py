import requests
import json
from datetime import datetime

def debug_frontend_request():
    """Debug-Skript um zu sehen, was das Frontend sendet"""
    
    # API Base URL
    base_url = "http://localhost:8000/api/v1"
    
    # Login um Token zu bekommen
    login_data = {
        "username": "test@buildwise.de",
        "password": "test123"
    }
    
    try:
        # Login
        print("🔧 Versuche Login...")
        login_response = requests.post(f"{base_url}/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        print("✅ Login erfolgreich")
        print(f"📋 Token: {token[:20]}...")
        
        # Simuliere den exakten Frontend-Request
        from requests_toolbelt import MultipartEncoder
        
        # Exakt wie im Frontend
        milestone_data = MultipartEncoder(
            fields={
                'title': 'Test Gewerk Frontend Debug',
                'description': 'Test Beschreibung vom Frontend Debug',
                'category': 'electrical',
                'priority': 'medium',
                'planned_date': '2024-12-31',
                'notes': 'Test Notizen vom Frontend Debug',
                'requires_inspection': 'false',
                'project_id': '1',
                'document_ids': '[]',
                'shared_document_ids': '[]'
            }
        )
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": milestone_data.content_type
        }
        
        print("🔧 Sende Frontend-Request...")
        print(f"📋 URL: {base_url}/milestones/with-documents")
        print(f"📋 Headers: {headers}")
        print(f"📋 Content-Type: {milestone_data.content_type}")
        print(f"📋 FormData Fields:")
        for field in milestone_data.fields:
            print(f"    - {field[0]}: {field[1]}")
        
        create_response = requests.post(
            f"{base_url}/milestones/with-documents", 
            data=milestone_data,
            headers=headers
        )
        
        print(f"\n📊 Response Status: {create_response.status_code}")
        print(f"📊 Response Headers: {dict(create_response.headers)}")
        print(f"📊 Response Body: {create_response.text}")
        
        if create_response.status_code == 201:
            print("✅ Milestone erfolgreich erstellt!")
            milestone = create_response.json()
            print(f"📋 Erstelltes Milestone: ID={milestone.get('id')}, Titel={milestone.get('title')}")
            
            # Überprüfe in der Datenbank
            print("\n🔧 Überprüfe Datenbank...")
            import aiosqlite
            import asyncio
            
            async def check_db():
                async with aiosqlite.connect('buildwise.db') as db:
                    cursor = await db.execute("""
                        SELECT id, title, category, status, created_at 
                        FROM milestones 
                        ORDER BY created_at DESC 
                        LIMIT 3
                    """)
                    milestones = await cursor.fetchall()
                    
                    print("📋 Letzte 3 Milestones in der Datenbank:")
                    for milestone in milestones:
                        print(f"  - ID: {milestone[0]}, Titel: {milestone[1]}, Kategorie: {milestone[2]}, Status: {milestone[3]}, Erstellt: {milestone[4]}")
            
            asyncio.run(check_db())
        else:
            print(f"❌ Fehler beim Erstellen des Milestones: {create_response.status_code}")
            
    except Exception as e:
        print(f"❌ Fehler beim Debug-Test: {e}")

if __name__ == "__main__":
    debug_frontend_request() 