#!/usr/bin/env python3
"""
Test-Skript für Microsoft OAuth Frontend-Simulation
Simuliert das Frontend-Verhalten
"""

import asyncio
import aiohttp
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_microsoft_frontend_simulation():
    """Simuliert das Frontend-Verhalten für Microsoft OAuth"""
    
    print("🧪 Microsoft OAuth Frontend-Simulation")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Teste den OAuth URL-Endpunkt (wie das Frontend es macht)
            print("📋 1. Teste OAuth URL-Endpunkt...")
            
            url = "http://localhost:8000/api/v1/auth/oauth/microsoft/url"
            headers = {
                'Content-Type': 'application/json',
            }
            
            async with session.get(url, headers=headers) as response:
                print(f"   - Status: {response.status}")
                print(f"   - Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   - Response: {data}")
                    
                    # 2. Teste die generierte OAuth URL
                    oauth_url = data.get('oauth_url')
                    if oauth_url:
                        print(f"\n📋 2. Generierte OAuth URL:")
                        print(f"   - URL: {oauth_url}")
                        
                        # 3. Teste die URL-Struktur
                        if 'login.microsoftonline.com' in oauth_url:
                            print("   ✅ Microsoft OAuth URL ist korrekt")
                        else:
                            print("   ❌ Microsoft OAuth URL ist fehlerhaft")
                        
                        # 4. Teste URL-Parameter
                        if 'client_id=' in oauth_url and 'redirect_uri=' in oauth_url:
                            print("   ✅ URL-Parameter sind vorhanden")
                        else:
                            print("   ❌ URL-Parameter fehlen")
                    else:
                        print("   ❌ OAuth URL fehlt in der Antwort")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Fehler: {error_text}")
            
            # 5. Teste CORS-Header
            print("\n📋 3. Teste CORS-Header...")
            async with session.options(url) as response:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                }
                print(f"   - CORS Headers: {cors_headers}")
                
                if cors_headers['Access-Control-Allow-Origin']:
                    print("   ✅ CORS ist konfiguriert")
                else:
                    print("   ⚠️ CORS könnte ein Problem sein")
            
            # 6. Teste Browser-Simulation
            print("\n📋 4. Browser-Simulation...")
            browser_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            }
            
            async with session.get(url, headers=browser_headers) as response:
                print(f"   - Browser-Simulation Status: {response.status}")
                if response.status == 200:
                    print("   ✅ Browser-Simulation erfolgreich")
                else:
                    print("   ❌ Browser-Simulation fehlgeschlagen")
        
        print("\n✅ Frontend-Simulation abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Frontend-Simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_browser_cache_issue():
    """Testet mögliche Browser-Cache-Probleme"""
    
    print("\n🔍 Browser-Cache-Test:")
    print("=" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Teste mit verschiedenen Cache-Headers
            cache_headers = [
                {'Cache-Control': 'no-cache'},
                {'Cache-Control': 'no-store'},
                {'Pragma': 'no-cache'},
                {},  # Keine Cache-Header
            ]
            
            for i, headers in enumerate(cache_headers, 1):
                print(f"   Test {i}: {headers}")
                async with session.get("http://localhost:8000/api/v1/auth/oauth/microsoft/url", headers=headers) as response:
                    print(f"      Status: {response.status}")
                    
    except Exception as e:
        print(f"   ❌ Cache-Test fehlgeschlagen: {e}")

async def main():
    """Hauptfunktion"""
    print("🧪 Microsoft OAuth Frontend-Test")
    print("=" * 50)
    
    # Frontend-Simulation
    success = await test_microsoft_frontend_simulation()
    
    if success:
        # Cache-Test
        await test_browser_cache_issue()
    
    print("\n💡 Empfehlungen für das Frontend:")
    print("   1. Browser-Cache leeren (Ctrl+F5)")
    print("   2. Entwicklertools öffnen und Network-Tab prüfen")
    print("   3. CORS-Fehler in der Konsole prüfen")
    print("   4. Mit Inkognito-Modus testen")

if __name__ == "__main__":
    asyncio.run(main()) 