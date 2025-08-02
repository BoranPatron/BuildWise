import requests
import json
from datetime import datetime

def test_milestone_documents_api():
    """Testet die Milestone-Dokumente API"""
    
    # API Base URL
    base_url = "http://localhost:8000/api/v1"
    
    # Login um Token zu bekommen - verwende Bauträger-Benutzer
    login_data = {
        "username": "janina.hankus@momentumvisual.de",
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
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Teste Milestones abrufen
        print("\n🔧 Versuche Milestones abzurufen...")
        list_response = requests.get(
            f"{base_url}/milestones/all",
            headers=headers
        )
        
        print(f"📊 List Response Status: {list_response.status_code}")
        print(f"📊 Response Headers: {dict(list_response.headers)}")
        print(f"📊 Response Body: {list_response.text[:500]}...")
        
        if list_response.status_code == 200:
            milestones = list_response.json()
            print(f"📋 Anzahl Milestones: {len(milestones)}")
            
            if len(milestones) > 0:
                print(f"📋 Erste 3 Milestones:")
                for i, milestone in enumerate(milestones[:3]):
                    print(f"  {i+1}. ID: {milestone.get('id')}, Titel: {milestone.get('title')}, Kategorie: {milestone.get('category')}")
                    documents = milestone.get('documents', [])
                    print(f"     Dokumente: {len(documents)}")
            
            # Suche nach Milestone ID 8 (mit Test-Dokumenten)
            milestone_8 = None
            for milestone in milestones:
                if milestone.get('id') == 8:
                    milestone_8 = milestone
                    break
            
            if milestone_8:
                print(f"\n📋 Milestone ID 8 gefunden:")
                print(f"  - Titel: {milestone_8.get('title')}")
                print(f"  - Kategorie: {milestone_8.get('category')}")
                print(f"  - Status: {milestone_8.get('status')}")
                
                documents = milestone_8.get('documents', [])
                print(f"  - Dokumente: {len(documents)} gefunden")
                
                if documents:
                    print("  📄 Dokumente Details:")
                    for i, doc in enumerate(documents):
                        print(f"    {i+1}. {doc.get('title', 'Unbekannt')}")
                        print(f"       - Datei: {doc.get('file_name', 'Unbekannt')}")
                        print(f"       - Typ: {doc.get('mime_type', 'Unbekannt')}")
                        print(f"       - Größe: {doc.get('file_size', 0)} Bytes")
                else:
                    print("  ❌ Keine Dokumente gefunden")
            else:
                print("❌ Milestone ID 8 nicht gefunden")
                
        else:
            print(f"❌ Fehler beim Abrufen der Milestones: {list_response.status_code}")
            print(f"Response: {list_response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")

if __name__ == "__main__":
    test_milestone_documents_api() 