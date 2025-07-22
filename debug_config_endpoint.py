#!/usr/bin/env python3
"""
Debug-Skript für den BuildWise-Fees-Config-Endpunkt
"""

import asyncio
import aiohttp
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def debug_config_endpoint():
    """Debuggt den Config-Endpunkt"""
    
    print("🔍 Debug BuildWise-Fees-Config-Endpunkt")
    print("=" * 50)
    
    try:
        # 1. Teste Backend-Service direkt
        print("📋 1. Teste Backend-Service direkt:")
        from app.core.config import settings
        from app.schemas.buildwise_fee import BuildWiseFeeConfigResponse
        
        print(f"   - Settings fee_percentage: {settings.buildwise_fee_percentage}")
        print(f"   - Settings fee_phase: {settings.buildwise_fee_phase}")
        print(f"   - Settings fee_enabled: {settings.buildwise_fee_enabled}")
        
        # 2. Teste Schema-Validierung
        print("\n📋 2. Teste Schema-Validierung:")
        try:
            config_response = BuildWiseFeeConfigResponse(
                fee_percentage=settings.buildwise_fee_percentage,
                fee_phase=settings.buildwise_fee_phase,
                fee_enabled=settings.buildwise_fee_enabled
            )
            print(f"   ✅ Schema-Validierung erfolgreich: {config_response}")
        except Exception as e:
            print(f"   ❌ Schema-Validierung fehlgeschlagen: {e}")
        
        # 3. Teste API-Endpunkt
        print("\n📋 3. Teste API-Endpunkt:")
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8000/api/v1/buildwise-fees/config"
            
            async with session.get(url) as response:
                print(f"   - Status: {response.status}")
                print(f"   - Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   - Response: {data}")
                else:
                    error_text = await response.text()
                    print(f"   - Error: {error_text}")
        
        # 4. Teste verschiedene URL-Varianten
        print("\n📋 4. Teste verschiedene URL-Varianten:")
        urls_to_test = [
            "http://localhost:8000/api/v1/buildwise-fees/config",
            "http://localhost:8000/buildwise-fees/config",
            "http://localhost:8000/api/v1/buildwise-fees/config/",
        ]
        
        for url in urls_to_test:
            try:
                async with session.get(url) as response:
                    print(f"   - {url}: {response.status}")
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"      Error: {error_text}")
            except Exception as e:
                print(f"   - {url}: ERROR - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Debug: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_config_schema():
    """Testet das Config-Schema"""
    
    print("\n🔍 Teste Config-Schema:")
    print("=" * 30)
    
    try:
        from app.schemas.buildwise_fee import BuildWiseFeeConfigResponse
        
        # Teste verschiedene Werte
        test_cases = [
            {
                "fee_percentage": 4.0,
                "fee_phase": "production",
                "fee_enabled": True
            },
            {
                "fee_percentage": 0.0,
                "fee_phase": "beta",
                "fee_enabled": False
            },
            {
                "fee_percentage": 1.0,
                "fee_phase": "beta",
                "fee_enabled": True
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                config = BuildWiseFeeConfigResponse(**test_case)
                print(f"   Test {i}: ✅ {config}")
            except Exception as e:
                print(f"   Test {i}: ❌ {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Schema-Test: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🧪 BuildWise-Fees-Config Debug")
    print("=" * 50)
    
    # 1. Debug Config-Endpunkt
    await debug_config_endpoint()
    
    # 2. Teste Config-Schema
    await test_config_schema()
    
    print("\n💡 Empfehlungen:")
    print("   1. Prüfen Sie die Backend-Logs")
    print("   2. Prüfen Sie das Schema")
    print("   3. Prüfen Sie die Settings")

if __name__ == "__main__":
    asyncio.run(main()) 