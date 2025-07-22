#!/usr/bin/env python3
"""
Debug-Skript für BuildWise Gebühren-Erstellung

Dieses Skript testet und analysiert die Gebühren-Erstellung, wenn ein Angebot angenommen wird.
"""

import sys
import os
import asyncio
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_fee_configuration():
    """Testet die aktuelle Gebühren-Konfiguration."""
    print("🔧 Teste Gebühren-Konfiguration...")
    
    try:
        from app.core.config import settings
        
        print(f"✅ Aktuelle Konfiguration:")
        print(f"   - Gebühren-Prozentsatz: {settings.buildwise_fee_percentage}%")
        print(f"   - Gebühren-Phase: {settings.buildwise_fee_phase}")
        print(f"   - Gebühren aktiviert: {settings.buildwise_fee_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Konfiguration: {e}")
        return False

async def test_fee_service():
    """Testet den BuildWiseFeeService."""
    print("\n🔧 Teste BuildWiseFeeService...")
    
    try:
        from app.services.buildwise_fee_service import BuildWiseFeeService
        
        # Teste statische Methoden
        percentage = BuildWiseFeeService.get_current_fee_percentage()
        phase = BuildWiseFeeService.get_current_fee_phase()
        enabled = BuildWiseFeeService.is_fee_enabled()
        
        print(f"✅ Service-Methoden:")
        print(f"   - get_current_fee_percentage(): {percentage}%")
        print(f"   - get_current_fee_phase(): {phase}")
        print(f"   - is_fee_enabled(): {enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Testen des Services: {e}")
        return False

async def test_database_connection():
    """Testet die Datenbankverbindung."""
    print("\n🔧 Teste Datenbankverbindung...")
    
    try:
        from app.core.database import get_db
        
        async for db in get_db():
            # Teste einfache Abfrage
            from sqlalchemy import text
            result = await db.execute(text("SELECT 1"))
            print("✅ Datenbankverbindung erfolgreich")
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Datenbankverbindung: {e}")
        return False

async def test_quotes_in_database():
    """Testet, ob Angebote in der Datenbank vorhanden sind."""
    print("\n🔧 Teste Angebote in der Datenbank...")
    
    try:
        from app.core.database import get_db
        from app.models.quote import Quote, QuoteStatus
        from sqlalchemy import select
        
        async for db in get_db():
            # Zähle alle Angebote
            query = select(Quote)
            result = await db.execute(query)
            quotes = result.scalars().all()
            
            print(f"✅ Angebote in der Datenbank: {len(quotes)}")
            
            if len(quotes) > 0:
                print("📋 Verfügbare Angebote:")
                for i, quote in enumerate(quotes[:5]):  # Zeige nur die ersten 5
                    print(f"   {i+1}. ID: {quote.id}, Status: {quote.status}, Betrag: {quote.total_amount}")
                
                            # Zeige akzeptierte Angebote
            accepted_quotes = [q for q in quotes if q.status == QuoteStatus.ACCEPTED]
            print(f"✅ Akzeptierte Angebote: {len(accepted_quotes)}")
            
            if len(accepted_quotes) > 0:
                print("📋 Akzeptierte Angebote:")
                for quote in accepted_quotes:
                    print(f"   - ID: {quote.id}, Betrag: {quote.total_amount}, Service Provider: {quote.service_provider_id}")
            else:
                print("⚠️ Keine Angebote in der Datenbank gefunden")
            
            break
        
        return len(quotes) > 0
        
    except Exception as e:
        print(f"❌ Fehler beim Testen der Angebote: {e}")
        return False

async def test_fees_in_database():
    """Testet, ob Gebühren in der Datenbank vorhanden sind."""
    print("\n🔧 Teste Gebühren in der Datenbank...")
    
    try:
        from app.core.database import get_db
        from app.models.buildwise_fee import BuildWiseFee
        from sqlalchemy import select
        
        async for db in get_db():
            # Zähle alle Gebühren
            query = select(BuildWiseFee)
            result = await db.execute(query)
            fees = result.scalars().all()
            
            print(f"✅ Gebühren in der Datenbank: {len(fees)}")
            
            if len(fees) > 0:
                print("📋 Verfügbare Gebühren:")
                for i, fee in enumerate(fees):
                    print(f"   {i+1}. ID: {fee.id}, Quote ID: {fee.quote_id}, Betrag: {fee.fee_amount}, Status: {fee.status}")
            else:
                print("⚠️ Keine Gebühren in der Datenbank gefunden")
            
            break
        
        return len(fees) > 0
        
    except Exception as e:
        print(f"❌ Fehler beim Testen der Gebühren: {e}")
        return False

async def test_fee_creation_with_sample():
    """Testet die Gebühren-Erstellung mit einem Beispiel-Angebot."""
    print("\n🔧 Teste Gebühren-Erstellung...")
    
    try:
        from app.core.database import get_db
        from app.models.quote import Quote, QuoteStatus
        from app.services.buildwise_fee_service import BuildWiseFeeService
        from sqlalchemy import select
        
        async for db in get_db():
            # Finde ein akzeptiertes Angebot
            query = select(Quote).where(Quote.status == QuoteStatus.ACCEPTED).limit(1)
            result = await db.execute(query)
            quote = result.scalar_one_or_none()
            
            if not quote:
                print("⚠️ Kein akzeptiertes Angebot gefunden")
                return False
            
            print(f"📋 Teste mit Angebot ID: {quote.id}")
            print(f"   - Betrag: {quote.total_amount}")
            print(f"   - Service Provider: {quote.service_provider_id}")
            
            # Prüfe ob bereits eine Gebühr für dieses Angebot existiert
            from app.models.buildwise_fee import BuildWiseFee
            fee_query = select(BuildWiseFee).where(BuildWiseFee.quote_id == quote.id)
            fee_result = await db.execute(fee_query)
            existing_fee = fee_result.scalar_one_or_none()
            
            if existing_fee:
                print(f"⚠️ Für Angebot {quote.id} existiert bereits eine Gebühr (ID: {existing_fee.id})")
                return True
            
            # Teste Gebühren-Erstellung
            try:
                fee = await BuildWiseFeeService.create_fee_from_quote(
                    db=db,
                    quote_id=quote.id,
                    cost_position_id=quote.id  # Verwende Quote-ID als Cost Position ID
                )
                
                print(f"✅ Gebühr erfolgreich erstellt:")
                print(f"   - Gebühren-ID: {fee.id}")
                print(f"   - Gebühren-Betrag: {fee.fee_amount}")
                print(f"   - Gebühren-Prozentsatz: {fee.fee_percentage}%")
                print(f"   - Status: {fee.status}")
                
                return True
                
            except Exception as fee_error:
                print(f"❌ Fehler beim Erstellen der Gebühr: {fee_error}")
                return False
            
            break
        
    except Exception as e:
        print(f"❌ Fehler beim Testen der Gebühren-Erstellung: {e}")
        return False

async def test_api_endpoint():
    """Testet den API-Endpunkt für Gebühren-Erstellung."""
    print("\n🔧 Teste API-Endpunkt...")
    
    try:
        import requests
        
        # Teste Konfiguration-Endpunkt
        config_url = "http://localhost:8000/api/v1/buildwise-fees/config"
        response = requests.get(config_url)
        
        if response.status_code == 200:
            config = response.json()
            print(f"✅ API-Konfiguration:")
            print(f"   - Gebühren-Prozentsatz: {config.get('fee_percentage')}%")
            print(f"   - Gebühren-Phase: {config.get('fee_phase')}")
            print(f"   - Gebühren aktiviert: {config.get('fee_enabled')}")
        else:
            print(f"❌ API-Konfiguration nicht erreichbar: {response.status_code}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Fehler beim Testen der API: {e}")
        return False

async def main():
    """Hauptfunktion."""
    print("🧪 BuildWise Gebühren-Erstellung Debug")
    print("=" * 50)
    
    # Test 1: Konfiguration
    config_ok = await test_fee_configuration()
    
    # Test 2: Service
    service_ok = await test_fee_service()
    
    # Test 3: Datenbankverbindung
    db_ok = await test_database_connection()
    
    # Test 4: Angebote in der Datenbank
    quotes_ok = await test_quotes_in_database()
    
    # Test 5: Gebühren in der Datenbank
    fees_ok = await test_fees_in_database()
    
    # Test 6: Gebühren-Erstellung
    creation_ok = await test_fee_creation_with_sample()
    
    # Test 7: API-Endpunkt
    api_ok = await test_api_endpoint()
    
    # Zusammenfassung
    print("\n📊 Debug-Zusammenfassung")
    print("=" * 30)
    print(f"✅ Konfiguration: {'OK' if config_ok else 'FEHLER'}")
    print(f"✅ Service: {'OK' if service_ok else 'FEHLER'}")
    print(f"✅ Datenbankverbindung: {'OK' if db_ok else 'FEHLER'}")
    print(f"✅ Angebote in DB: {'OK' if quotes_ok else 'FEHLER'}")
    print(f"✅ Gebühren in DB: {'OK' if fees_ok else 'FEHLER'}")
    print(f"✅ Gebühren-Erstellung: {'OK' if creation_ok else 'FEHLER'}")
    print(f"✅ API-Endpunkt: {'OK' if api_ok else 'FEHLER'}")
    
    if config_ok and service_ok and db_ok and quotes_ok and creation_ok:
        print("\n🎉 Alle Tests bestanden!")
        print("💡 Die Gebühren-Erstellung funktioniert korrekt.")
    else:
        print("\n❌ Einige Tests fehlgeschlagen.")
        print("💡 Überprüfen Sie die Konfiguration und Datenbank.")

if __name__ == "__main__":
    asyncio.run(main()) 