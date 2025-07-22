#!/usr/bin/env python3
"""
Debug-Skript für Frontend-API-Problem bei BuildWise-Gebühren
"""

import asyncio
import aiohttp
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_frontend_api_calls():
    """Simuliert die Frontend-API-Aufrufe"""
    
    print("🧪 Frontend-API-Test für BuildWise-Gebühren")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            print(f"📅 Aktueller Monat/Year: {current_month}/{current_year}")
            
            # 1. Teste API-Endpunkt ohne Filter
            print("\n📋 1. Teste API ohne Filter:")
            url_no_filter = "http://localhost:8000/api/v1/buildwise-fees/"
            
            async with session.get(url_no_filter) as response:
                print(f"   - Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   - Anzahl Gebühren: {len(data)}")
                    if len(data) > 0:
                        print(f"   - Erste Gebühr: ID={data[0].get('id')}, Amount={data[0].get('fee_amount')}")
                else:
                    error_text = await response.text()
                    print(f"   - Error: {error_text}")
            
            # 2. Teste API mit Monat/Year-Filter
            print(f"\n📋 2. Teste API mit Monat/Year-Filter ({current_month}/{current_year}):")
            url_with_filter = f"http://localhost:8000/api/v1/buildwise-fees/?month={current_month}&year={current_year}"
            
            async with session.get(url_with_filter) as response:
                print(f"   - Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   - Anzahl Gebühren: {len(data)}")
                    if len(data) > 0:
                        print(f"   - Erste Gebühr: ID={data[0].get('id')}, Amount={data[0].get('fee_amount')}")
                else:
                    error_text = await response.text()
                    print(f"   - Error: {error_text}")
            
            # 3. Teste API mit verschiedenen Headers (wie Frontend)
            print("\n📋 3. Teste API mit Frontend-Headers:")
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            async with session.get(url_with_filter, headers=headers) as response:
                print(f"   - Status: {response.status}")
                print(f"   - Headers: {dict(response.headers)}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   - Anzahl Gebühren: {len(data)}")
                else:
                    error_text = await response.text()
                    print(f"   - Error: {error_text}")
            
            # 4. Teste CORS-Header
            print("\n📋 4. Teste CORS-Header:")
            async with session.options(url_with_filter) as response:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                }
                print(f"   - CORS Headers: {cors_headers}")
            
            # 5. Teste verschiedene URL-Varianten
            print("\n📋 5. Teste verschiedene URL-Varianten:")
            urls_to_test = [
                "http://localhost:8000/api/v1/buildwise-fees/",
                "http://localhost:8000/api/v1/buildwise-fees",
                "http://localhost:8000/buildwise-fees/",
                "http://localhost:8000/buildwise-fees",
            ]
            
            for url in urls_to_test:
                try:
                    async with session.get(url) as response:
                        print(f"   - {url}: {response.status}")
                except Exception as e:
                    print(f"   - {url}: ERROR - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_backend_direct():
    """Testet das Backend direkt"""
    
    print("\n🔍 Backend-Direkttest:")
    print("=" * 30)
    
    try:
        from app.core.database import get_db
        from app.services.buildwise_fee_service import BuildWiseFeeService
        
        async for db in get_db():
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            print(f"📅 Teste mit Monat/Year: {current_month}/{current_year}")
            
            # Teste Service direkt
            fees = await BuildWiseFeeService.get_fees(
                db, month=current_month, year=current_year
            )
            
            print(f"   - Gefundene Gebühren: {len(fees)}")
            if len(fees) > 0:
                for i, fee in enumerate(fees):
                    print(f"     Gebühr {i+1}: ID={fee.id}, Amount={fee.fee_amount}, Status={fee.status}")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Backend-Test: {e}")
        return False

async def test_api_endpoint():
    """Testet den API-Endpunkt direkt"""
    
    print("\n🔍 API-Endpunkt-Test:")
    print("=" * 30)
    
    try:
        from app.api.buildwise_fee import router
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Teste GET /buildwise-fees/
        response = client.get(f"/api/v1/buildwise-fees/?month={current_month}&year={current_year}")
        
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   - Anzahl Gebühren: {len(data)}")
            if len(data) > 0:
                print(f"   - Erste Gebühr: {data[0]}")
        else:
            print(f"   - Error Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim API-Endpunkt-Test: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🧪 Frontend-API-Problem Debug")
    print("=" * 50)
    
    # 1. Teste Frontend-API-Aufrufe
    await test_frontend_api_calls()
    
    # 2. Teste Backend direkt
    await test_backend_direct()
    
    # 3. Teste API-Endpunkt
    await test_api_endpoint()
    
    print("\n💡 Empfehlungen:")
    print("   1. Prüfen Sie die Browser-Konsole auf CORS-Fehler")
    print("   2. Prüfen Sie die Network-Tab im Browser")
    print("   3. Prüfen Sie die Backend-Logs")
    print("   4. Testen Sie mit Postman oder curl")

if __name__ == "__main__":
    asyncio.run(main()) 