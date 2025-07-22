#!/usr/bin/env python3
"""
Skript zur Analyse und Behebung des Gebühren-Anzeige-Problems
"""

import sys
import os
import asyncio
from datetime import datetime, date

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def analyze_fee_display_issue():
    """Analysiert das Gebühren-Anzeige-Problem"""
    
    print("🔍 Analyse des Gebühren-Anzeige-Problems")
    print("=" * 50)
    
    try:
        from app.core.database import get_db
        from app.models.buildwise_fee import BuildWiseFee
        from app.services.buildwise_fee_service import BuildWiseFeeService
        from sqlalchemy import select
        
        async for db in get_db():
            # 1. Alle Gebühren in der Datenbank auflisten
            print("📋 1. Alle Gebühren in der Datenbank:")
            query = select(BuildWiseFee)
            result = await db.execute(query)
            all_fees = result.scalars().all()
            
            print(f"   Gesamtanzahl Gebühren: {len(all_fees)}")
            
            for i, fee in enumerate(all_fees):
                print(f"   Gebühr {i+1}:")
                print(f"     - ID: {fee.id}")
                print(f"     - Project ID: {fee.project_id}")
                print(f"     - Service Provider ID: {fee.service_provider_id}")
                print(f"     - Status: {fee.status}")
                print(f"     - Betrag: {fee.fee_amount}")
                print(f"     - Prozentsatz: {fee.fee_percentage}%")
                print(f"     - Created At: {fee.created_at}")
                print(f"     - Invoice Date: {fee.invoice_date}")
                print()
            
            # 2. Aktueller Monat/Year
            current_month = datetime.now().month
            current_year = datetime.now().year
            print(f"📅 2. Aktueller Monat/Year: {current_month}/{current_year}")
            
            # 3. Teste Backend-Service mit verschiedenen Filtern
            print("\n📋 3. Teste Backend-Service:")
            
            # Teste ohne Filter
            print("   a) Ohne Filter:")
            fees_no_filter = await BuildWiseFeeService.get_fees(db)
            print(f"      Gefunden: {len(fees_no_filter)} Gebühren")
            
            # Teste mit aktuellem Monat/Year
            print(f"   b) Mit aktuellem Monat/Year ({current_month}/{current_year}):")
            fees_current_month = await BuildWiseFeeService.get_fees(
                db, month=current_month, year=current_year
            )
            print(f"      Gefunden: {len(fees_current_month)} Gebühren")
            
            # Teste mit Juli 2025 (Datum der Gebühr)
            print("   c) Mit Juli 2025 (Datum der Gebühr):")
            fees_july_2025 = await BuildWiseFeeService.get_fees(
                db, month=7, year=2025
            )
            print(f"      Gefunden: {len(fees_july_2025)} Gebühren")
            
            # 4. Analysiere das Datum-Problem
            print("\n📋 4. Datum-Analyse:")
            if all_fees:
                fee = all_fees[0]
                created_at = fee.created_at
                invoice_date = fee.invoice_date
                
                print(f"   - Created At: {created_at}")
                print(f"   - Invoice Date: {invoice_date}")
                print(f"   - Ist Created At in der Zukunft? {created_at > datetime.now()}")
                print(f"   - Ist Invoice Date in der Zukunft? {invoice_date and invoice_date > date.today()}")
                
                # 5. Lösungsvorschläge
                print("\n📋 5. Lösungsvorschläge:")
                
                if created_at > datetime.now():
                    print("   ❌ Problem: Created At ist in der Zukunft!")
                    print("   💡 Lösung: Created At auf aktuelles Datum setzen")
                
                if invoice_date and invoice_date > date.today():
                    print("   ❌ Problem: Invoice Date ist in der Zukunft!")
                    print("   💡 Lösung: Invoice Date auf aktuelles Datum setzen")
                
                if not created_at or created_at > datetime.now():
                    print("   🔧 Empfohlene Aktion: Datum korrigieren")
                else:
                    print("   ✅ Datum ist korrekt")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Analyse: {e}")
        import traceback
        traceback.print_exc()
        return False

async def fix_fee_dates():
    """Korrigiert die Datums-Probleme der Gebühren"""
    
    print("\n🔧 Korrigiere Gebühren-Daten...")
    print("=" * 40)
    
    try:
        from app.core.database import get_db
        from app.models.buildwise_fee import BuildWiseFee
        from sqlalchemy import select, update
        
        async for db in get_db():
            # Finde alle Gebühren mit zukünftigen Daten
            query = select(BuildWiseFee).where(
                (BuildWiseFee.created_at > datetime.now()) |
                (BuildWiseFee.invoice_date > date.today())
            )
            result = await db.execute(query)
            problematic_fees = result.scalars().all()
            
            print(f"📋 Gefundene problematische Gebühren: {len(problematic_fees)}")
            
            if len(problematic_fees) > 0:
                # Korrigiere die Daten
                current_datetime = datetime.now()
                current_date = date.today()
                
                for fee in problematic_fees:
                    print(f"   🔧 Korrigiere Gebühr ID {fee.id}:")
                    print(f"      - Created At: {fee.created_at} → {current_datetime}")
                    print(f"      - Invoice Date: {fee.invoice_date} → {current_date}")
                    
                    # Update der Gebühr
                    update_query = update(BuildWiseFee).where(
                        BuildWiseFee.id == fee.id
                    ).values(
                        created_at=current_datetime,
                        invoice_date=current_date,
                        updated_at=current_datetime
                    )
                    
                    await db.execute(update_query)
                
                await db.commit()
                print("   ✅ Gebühren-Daten erfolgreich korrigiert!")
            else:
                print("   ✅ Keine problematischen Gebühren gefunden")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Korrigieren der Daten: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fee_display():
    """Testet die Gebühren-Anzeige nach der Korrektur"""
    
    print("\n🧪 Teste Gebühren-Anzeige...")
    print("=" * 40)
    
    try:
        from app.core.database import get_db
        from app.services.buildwise_fee_service import BuildWiseFeeService
        
        async for db in get_db():
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            print(f"📅 Teste mit aktuellem Monat/Year: {current_month}/{current_year}")
            
            # Teste ohne Filter
            fees_no_filter = await BuildWiseFeeService.get_fees(db)
            print(f"   - Ohne Filter: {len(fees_no_filter)} Gebühren")
            
            # Teste mit aktuellem Monat/Year
            fees_current_month = await BuildWiseFeeService.get_fees(
                db, month=current_month, year=current_year
            )
            print(f"   - Mit aktuellem Monat/Year: {len(fees_current_month)} Gebühren")
            
            if len(fees_current_month) > 0:
                print("   ✅ Gebühren werden jetzt korrekt angezeigt!")
            else:
                print("   ❌ Gebühren werden immer noch nicht angezeigt")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🧪 Gebühren-Anzeige-Problem Analyse und Fix")
    print("=" * 60)
    
    # 1. Analysiere das Problem
    await analyze_fee_display_issue()
    
    # 2. Korrigiere die Daten
    await fix_fee_dates()
    
    # 3. Teste die Anzeige
    await test_fee_display()
    
    print("\n🎉 Analyse und Fix abgeschlossen!")
    print("💡 Überprüfen Sie jetzt die Dienstleisteransicht unter 'Gebühren'")

if __name__ == "__main__":
    asyncio.run(main()) 