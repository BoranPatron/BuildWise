#!/usr/bin/env python3
"""Test-Skript um Angebote für milestone_id=1 zu prüfen"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.quote_service import get_quotes_for_milestone

async def test_quotes_direct_db():
    """Teste direkten Datenbank-Zugriff"""
    print("\n" + "="*80)
    print("1. DIREKTER DATENBANK-TEST")
    print("="*80)
    
    # Synchrone Verbindung für direkte SQL-Abfragen
    sync_engine = create_engine(settings.database_url)
    
    with sync_engine.connect() as conn:
        # Prüfe alle Quotes
        result = conn.execute(text("SELECT id, milestone_id, service_provider_id, status, total_amount FROM quotes"))
        quotes = result.fetchall()
        print(f"\n📊 Alle Quotes in der Datenbank:")
        for quote in quotes:
            print(f"   Quote ID: {quote[0]}, Milestone: {quote[1]}, Provider: {quote[2]}, Status: {quote[3]}, Amount: {quote[4]}")
        
        # Prüfe spezifisch milestone_id=1
        result = conn.execute(text("SELECT * FROM quotes WHERE milestone_id = 1"))
        quotes_m1 = result.fetchall()
        print(f"\n🎯 Quotes für milestone_id=1: {len(quotes_m1)} gefunden")
        for quote in quotes_m1:
            print(f"   Quote: {quote}")

async def test_quotes_service():
    """Teste den Service-Layer"""
    print("\n" + "="*80)
    print("2. SERVICE-LAYER TEST")
    print("="*80)
    
    # Async Engine für Service-Tests  
    # SQLite braucht aiosqlite für async
    engine = create_async_engine(settings.database_url.replace('sqlite:///', 'sqlite+aiosqlite:///'))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Test get_quotes_for_milestone
        quotes = await get_quotes_for_milestone(db, 1)
        print(f"\n📦 get_quotes_for_milestone(1) returned: {len(quotes)} quotes")
        for quote in quotes:
            print(f"   Quote ID: {quote.id}, Status: {quote.status}, Amount: {quote.total_amount}")
            print(f"   Service Provider ID: {quote.service_provider_id}")
            print(f"   Company: {quote.company_name}, Contact: {quote.contact_person}")
    
    await engine.dispose()

async def test_api_endpoint():
    """Teste den API-Endpunkt"""
    print("\n" + "="*80)
    print("3. API-ENDPUNKT TEST")
    print("="*80)
    
    import httpx
    
    # Erstelle einen Test-Token (anpassen wenn nötig)
    base_url = "http://localhost:8000/api/v1"
    
    # Login als Bauträger
    async with httpx.AsyncClient() as client:
        # Versuche Login
        login_data = {
            "username": "bautraeger@example.com",  # Anpassen!
            "password": "password123"  # Anpassen!
        }
        
        try:
            login_response = await client.post(f"{base_url}/auth/login", data=login_data)
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                print(f"✅ Login erfolgreich, Token erhalten")
                
                # Teste den Endpunkt
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(f"{base_url}/quotes/milestone/1", headers=headers)
                
                print(f"\n🌐 API Response Status: {response.status_code}")
                if response.status_code == 200:
                    quotes = response.json()
                    print(f"📨 API returned {len(quotes)} quotes")
                    for quote in quotes:
                        print(f"   Quote: {quote}")
                else:
                    print(f"❌ API Error: {response.text}")
            else:
                print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
                print("   Bitte Credentials in test_api_endpoint() anpassen!")
        except Exception as e:
            print(f"❌ API Test fehlgeschlagen: {e}")
            print("   Ist der Backend-Server gestartet? (uvicorn app.main:app --reload)")

async def main():
    print("\n🔍 TESTE QUOTES FÜR MILESTONE_ID=1")
    print("="*80)
    
    # Test 1: Direkte DB
    await test_quotes_direct_db()
    
    # Test 2: Service Layer
    await test_quotes_service()
    
    # Test 3: API
    await test_api_endpoint()
    
    print("\n" + "="*80)
    print("✅ TESTS ABGESCHLOSSEN")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
