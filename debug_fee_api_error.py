#!/usr/bin/env python3
"""
Debug-Skript für den Gebühren-API-Fehler
"""

import sys
import os
import asyncio

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def debug_fee_api():
    """Debuggt den Gebühren-API-Fehler"""
    
    print("🔧 Debug Gebühren-API-Fehler")
    print("=" * 40)
    
    try:
        from app.core.database import get_db
        from app.services.buildwise_fee_service import BuildWiseFeeService
        from app.schemas.buildwise_fee import BuildWiseFeeResponse
        
        print("📋 1. Teste BuildWiseFeeService.get_fees direkt:")
        async for db in get_db():
            try:
                fees = await BuildWiseFeeService.get_fees(db)
                print(f"✅ Service erfolgreich: {len(fees)} Gebühren gefunden")
                
                for fee in fees:
                    print(f"  - ID: {fee.id}, Project: {fee.project_id}, Status: {fee.status}, Amount: {fee.fee_amount}")
                
            except Exception as e:
                print(f"❌ Service-Fehler: {e}")
                import traceback
                traceback.print_exc()
            
            break
        
        print("\n📋 2. Teste Schema-Konvertierung:")
        async for db in get_db():
            try:
                fees = await BuildWiseFeeService.get_fees(db)
                
                for fee in fees:
                    try:
                        response = BuildWiseFeeResponse.from_orm(fee)
                        print(f"✅ Schema-Konvertierung erfolgreich für Gebühr {fee.id}")
                    except Exception as schema_error:
                        print(f"❌ Schema-Fehler für Gebühr {fee.id}: {schema_error}")
                        import traceback
                        traceback.print_exc()
                
            except Exception as e:
                print(f"❌ Schema-Test-Fehler: {e}")
            
            break
        
        print("\n📋 3. Teste API-Endpunkt direkt:")
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8000/api/v1/buildwise-fees/"
                async with session.get(url) as response:
                    print(f"📋 API-Test:")
                    print(f"  - Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"  - Anzahl Gebühren: {len(data)}")
                        for fee in data:
                            print(f"    - ID: {fee.get('id')}, Project: {fee.get('project_id')}, Status: {fee.get('status')}")
                    else:
                        error_text = await response.text()
                        print(f"  - Error: {error_text}")
        
        except Exception as e:
            print(f"❌ API-Test-Fehler: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Debug: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_schema_issues():
    """Prüft Schema-Probleme"""
    
    print("\n📋 4. Prüfe Schema-Definitionen:")
    try:
        from app.schemas.buildwise_fee import BuildWiseFeeResponse
        from app.models.buildwise_fee import BuildWiseFee
        
        print("✅ BuildWiseFeeResponse Schema importiert")
        print("✅ BuildWiseFee Model importiert")
        
        # Prüfe Schema-Felder
        print("\n📋 Schema-Felder:")
        import inspect
        fields = inspect.getmembers(BuildWiseFeeResponse, lambda x: not inspect.isroutine(x))
        for field_name, field_value in fields:
            if not field_name.startswith('_'):
                print(f"  - {field_name}: {field_value}")
        
    except Exception as e:
        print(f"❌ Schema-Prüfung-Fehler: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Hauptfunktion"""
    print("🔧 Debug Gebühren-API-Fehler")
    print("=" * 50)
    
    # 1. Debug API-Fehler
    await debug_fee_api()
    
    # 2. Prüfe Schema-Probleme
    await check_schema_issues()
    
    print("\n💡 Nächste Schritte:")
    print("1. Backend-Logs überprüfen")
    print("2. Schema-Probleme beheben")
    print("3. Backend neu starten")

if __name__ == "__main__":
    asyncio.run(main()) 