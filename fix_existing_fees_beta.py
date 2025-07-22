#!/usr/bin/env python3
"""
Skript zur Korrektur bestehender Gebühren für die Beta-Phase

Dieses Skript korrigiert alle bestehenden Gebühren, die mit dem falschen
Prozentsatz (1% statt 0%) erstellt wurden.
"""

import sys
import os
import asyncio
from datetime import datetime
from decimal import Decimal

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def analyze_existing_fees():
    """Analysiert bestehende Gebühren in der Datenbank."""
    
    print("🔍 Analyse bestehender Gebühren")
    print("=" * 40)
    
    try:
        from app.core.database import get_db
        from app.models.buildwise_fee import BuildWiseFee
        from app.core.config import settings
        from sqlalchemy import select
        
        async for db in get_db():
            # Alle Gebühren abrufen
            query = select(BuildWiseFee)
            result = await db.execute(query)
            all_fees = result.scalars().all()
            
            print(f"📊 Gesamtanzahl Gebühren: {len(all_fees)}")
            
            if len(all_fees) == 0:
                print("✅ Keine Gebühren in der Datenbank gefunden")
                return
            
            # Analysiere jede Gebühr
            incorrect_fees = []
            correct_fees = []
            
            for fee in all_fees:
                print(f"\n📋 Gebühr ID {fee.id}:")
                print(f"   - Projekt: {fee.project_id}")
                print(f"   - Quote: {fee.quote_id}")
                print(f"   - Service Provider: {fee.service_provider_id}")
                print(f"   - Quote Amount: {fee.quote_amount}")
                print(f"   - Fee Percentage: {fee.fee_percentage}%")
                print(f"   - Fee Amount: {fee.fee_amount}")
                print(f"   - Status: {fee.status}")
                print(f"   - Created At: {fee.created_at}")
                
                # Prüfe ob Gebühr korrekt ist
                if settings.buildwise_fee_phase == "beta":
                    expected_percentage = 0.0
                    expected_amount = 0.0
                else:
                    expected_percentage = 4.0
                    expected_amount = float(fee.quote_amount) * 0.04
                
                if fee.fee_percentage != expected_percentage:
                    incorrect_fees.append({
                        'fee': fee,
                        'current_percentage': fee.fee_percentage,
                        'expected_percentage': expected_percentage,
                        'current_amount': fee.fee_amount,
                        'expected_amount': expected_amount
                    })
                    print(f"   ❌ FALSCH: {fee.fee_percentage}% statt {expected_percentage}%")
                else:
                    correct_fees.append(fee)
                    print(f"   ✅ KORREKT: {fee.fee_percentage}%")
            
            print(f"\n📊 Zusammenfassung:")
            print(f"   ✅ Korrekte Gebühren: {len(correct_fees)}")
            print(f"   ❌ Falsche Gebühren: {len(incorrect_fees)}")
            
            if len(incorrect_fees) > 0:
                print(f"\n🔧 Korrektur erforderlich für {len(incorrect_fees)} Gebühren")
                return incorrect_fees
            else:
                print("✅ Alle Gebühren sind korrekt!")
                return []
            
            break
        
        return []
        
    except Exception as e:
        print(f"❌ Fehler bei der Analyse: {e}")
        import traceback
        traceback.print_exc()
        return []

async def fix_existing_fees(incorrect_fees):
    """Korrigiert bestehende Gebühren mit dem falschen Prozentsatz."""
    
    print(f"\n🔧 Korrigiere {len(incorrect_fees)} Gebühren...")
    print("=" * 50)
    
    try:
        from app.core.database import get_db
        from app.models.buildwise_fee import BuildWiseFee
        from app.core.config import settings
        from sqlalchemy import update
        
        async for db in get_db():
            corrected_count = 0
            
            for fee_info in incorrect_fees:
                fee = fee_info['fee']
                expected_percentage = fee_info['expected_percentage']
                expected_amount = fee_info['expected_amount']
                
                print(f"\n🔧 Korrigiere Gebühr ID {fee.id}:")
                print(f"   - Alt: {fee.fee_percentage}% = {fee.fee_amount}")
                print(f"   - Neu: {expected_percentage}% = {expected_amount}")
                
                # Berechne neue Beträge
                if expected_percentage == 0.0:
                    # Beta-Phase: Alle Beträge auf 0 setzen
                    new_fee_amount = Decimal('0.00')
                    new_tax_amount = Decimal('0.00')
                    new_net_amount = Decimal('0.00')
                    new_gross_amount = Decimal('0.00')
                else:
                    # Production-Phase: 4% berechnen
                    quote_amount = float(fee.quote_amount)
                    new_fee_amount = Decimal(str(round(quote_amount * 0.04, 2)))
                    new_tax_amount = Decimal(str(round(float(new_fee_amount) * 0.19, 2)))
                    new_net_amount = new_fee_amount
                    new_gross_amount = new_fee_amount + new_tax_amount
                
                # Update der Gebühr
                update_query = update(BuildWiseFee).where(
                    BuildWiseFee.id == fee.id
                ).values(
                    fee_percentage=Decimal(str(expected_percentage)),
                    fee_amount=new_fee_amount,
                    tax_amount=new_tax_amount,
                    net_amount=new_net_amount,
                    gross_amount=new_gross_amount,
                    updated_at=datetime.now()
                )
                
                await db.execute(update_query)
                corrected_count += 1
                
                print(f"   ✅ Korrigiert!")
            
            await db.commit()
            print(f"\n✅ {corrected_count} Gebühren erfolgreich korrigiert!")
            
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Korrigieren: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_correction():
    """Verifiziert, dass die Korrektur erfolgreich war."""
    
    print(f"\n🔍 Verifiziere Korrektur...")
    print("=" * 30)
    
    try:
        from app.core.database import get_db
        from app.models.buildwise_fee import BuildWiseFee
        from app.core.config import settings
        from sqlalchemy import select
        
        async for db in get_db():
            # Alle Gebühren erneut abrufen
            query = select(BuildWiseFee)
            result = await db.execute(query)
            all_fees = result.scalars().all()
            
            print(f"📊 Überprüfe {len(all_fees)} Gebühren...")
            
            all_correct = True
            
            for fee in all_fees:
                if settings.buildwise_fee_phase == "beta":
                    expected_percentage = 0.0
                else:
                    expected_percentage = 4.0
                
                if fee.fee_percentage != expected_percentage:
                    print(f"   ❌ Gebühr ID {fee.id}: {fee.fee_percentage}% statt {expected_percentage}%")
                    all_correct = False
                else:
                    print(f"   ✅ Gebühr ID {fee.id}: {fee.fee_percentage}% (korrekt)")
            
            if all_correct:
                print(f"\n🎉 Alle Gebühren sind korrekt!")
            else:
                print(f"\n⚠️  Einige Gebühren sind noch falsch!")
            
            break
        
        return all_correct
        
    except Exception as e:
        print(f"❌ Fehler bei der Verifikation: {e}")
        return False

async def main():
    """Hauptfunktion"""
    print("🔧 BuildWise Gebühren-Korrektur für Beta-Phase")
    print("=" * 60)
    
    # 1. Analysiere bestehende Gebühren
    incorrect_fees = await analyze_existing_fees()
    
    if len(incorrect_fees) == 0:
        print("\n✅ Keine Korrektur erforderlich!")
        return
    
    # 2. Automatische Korrektur (ohne Bestätigung)
    print(f"\n🔧 Korrigiere {len(incorrect_fees)} Gebühren automatisch...")
    
    # 3. Korrigiere Gebühren
    success = await fix_existing_fees(incorrect_fees)
    
    if success:
        # 4. Verifiziere Korrektur
        await verify_correction()
        
        print("\n🎉 Korrektur abgeschlossen!")
        print("💡 Die Gebühren sollten jetzt korrekt in der Dienstleisteransicht angezeigt werden.")
    else:
        print("\n❌ Korrektur fehlgeschlagen!")

if __name__ == "__main__":
    asyncio.run(main()) 