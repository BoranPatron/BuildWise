#!/usr/bin/env python3
"""
Einfacher API-Test für Dokumente
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000/api/v1"
    
    # Test ohne Authentifizierung zuerst (um zu sehen ob Server läuft)
    try:
        print("🔍 Teste Server-Erreichbarkeit...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"✅ Server läuft - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Server nicht erreichbar: {e}")
        return
    
    # Login als Bauträger
    login_data = {
        "username": "bautraeger@test.com", 
        "password": "password123"
    }
    
    try:
        print("\n🔐 Login als Bauträger...")
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get("access_token")
            print(f"✅ Login erfolgreich")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Teste Milestones für verschiedene Projekte
            for project_id in [7, 8, 1]:
                print(f"\n📋 Teste Milestones für Projekt {project_id}...")
                
                try:
                    milestones_response = requests.get(
                        f"{base_url}/milestones", 
                        params={"project_id": project_id},
                        headers=headers
                    )
                    
                    if milestones_response.status_code == 200:
                        milestones = milestones_response.json()
                        print(f"✅ {len(milestones)} Milestones gefunden für Projekt {project_id}")
                        
                        for milestone in milestones:
                            print(f"\n📄 Milestone {milestone['id']}: {milestone['title']}")
                            documents = milestone.get('documents', [])
                            print(f"   📋 Dokumente: {len(documents) if isinstance(documents, list) else 'Nicht Liste'}")
                            
                            if documents:
                                if isinstance(documents, list):
                                    for i, doc in enumerate(documents):
                                        print(f"      {i+1}. {doc}")
                                else:
                                    print(f"   ⚠️ Dokumente sind kein Array: {type(documents)} - {documents}")
                            
                            # Teste auch Einzelabruf
                            single_response = requests.get(
                                f"{base_url}/milestones/{milestone['id']}", 
                                headers=headers
                            )
                            
                            if single_response.status_code == 200:
                                single_data = single_response.json()
                                single_docs = single_data.get('documents', [])
                                shared_docs = single_data.get('shared_document_ids', [])
                                print(f"   🔍 Einzelabruf - Dokumente: {len(single_docs) if isinstance(single_docs, list) else 'Nicht Liste'}")
                                print(f"   🔍 Einzelabruf - Shared Docs: {shared_docs}")
                                
                                if single_docs and isinstance(single_docs, list):
                                    print(f"   📋 Einzelabruf Dokumente:")
                                    for i, doc in enumerate(single_docs):
                                        print(f"      {i+1}. {doc}")
                            else:
                                print(f"   ❌ Einzelabruf fehlgeschlagen: {single_response.status_code}")
                    else:
                        print(f"❌ Milestones laden fehlgeschlagen: {milestones_response.status_code}")
                        print(f"   Response: {milestones_response.text[:200]}")
                        
                except Exception as e:
                    print(f"❌ Fehler bei Projekt {project_id}: {e}")
        else:
            print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Allgemeiner Fehler: {e}")

if __name__ == "__main__":
    test_api()