#!/usr/bin/env python3
"""
Test-Skript für die Login-Funktionalität nach der Datenbank-Reparatur
"""

import asyncio
import aiohttp
import json

async def test_login():
    """Testet die Login-Funktionalität"""
    
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Test-Daten für Service Provider
    test_data = {
        "username": "service_provider@test.com",
        "password": "test123"
    }
    
    print("🔍 Teste Login-Funktionalität...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_data) as response:
                print(f"📡 Response Status: {response.status}")
                print(f"📡 Response Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ Login erfolgreich!")
                    print(f"🔑 Token: {data.get('access_token', 'N/A')[:20]}...")
                    print(f"👤 User: {data.get('user', {}).get('email', 'N/A')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Login fehlgeschlagen: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Fehler beim Login-Test: {e}")
        return False

async def test_database_connection():
    """Testet die Datenbankverbindung"""
    
    url = "http://localhost:8000/api/v1/users/me"
    
    print("🔍 Teste Datenbankverbindung...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Erst Login für Token
            login_data = {
                "username": "service_provider@test.com",
                "password": "test123"
            }
            
            async with session.post("http://localhost:8000/api/v1/auth/login", json=login_data) as login_response:
                if login_response.status == 200:
                    login_result = await login_response.json()
                    token = login_result.get('access_token')
                    
                    # Teste Datenbankzugriff
                    headers = {"Authorization": f"Bearer {token}"}
                    async with session.get(url, headers=headers) as response:
                        print(f"📡 DB Test Status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print("✅ Datenbankverbindung funktioniert!")
                            print(f"👤 User: {data.get('email', 'N/A')}")
                            return True
                        else:
                            error_text = await response.text()
                            print(f"❌ Datenbankfehler: {error_text}")
                            return False
                else:
                    print("❌ Login für DB-Test fehlgeschlagen")
                    return False
                    
    except Exception as e:
        print(f"❌ Fehler beim DB-Test: {e}")
        return False

async def main():
    """Hauptfunktion für alle Tests"""
    
    print("🚀 Starte Login-Tests nach Datenbank-Reparatur...")
    
    # 1. Teste Login
    login_success = await test_login()
    
    # 2. Teste Datenbankverbindung
    db_success = await test_database_connection()
    
    # 3. Zusammenfassung
    print("\n📊 Test-Ergebnisse:")
    print(f"   Login: {'✅ Erfolgreich' if login_success else '❌ Fehlgeschlagen'}")
    print(f"   Datenbank: {'✅ Funktioniert' if db_success else '❌ Fehler'}")
    
    if login_success and db_success:
        print("\n🎉 Alle Tests erfolgreich! Login funktioniert wieder.")
    else:
        print("\n⚠️ Einige Tests fehlgeschlagen. Überprüfe die Logs.")

if __name__ == "__main__":
    asyncio.run(main()) 