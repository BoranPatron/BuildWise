#!/usr/bin/env python3
"""
Skript zur Überprüfung der BuildWise Gebühren in der Datenbank
"""

import asyncio
import sys
import os

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.buildwise_fee import BuildWiseFee
from sqlalchemy import select

async def check_buildwise_fees():
    """Überprüft die BuildWise Gebühren in der Datenbank."""
    
    print("🔍 Überprüfe BuildWise Gebühren in der Datenbank...")
    
    try:
        async for db in get_db():
            # Hole alle BuildWise Gebühren
            result = await db.execute(select(BuildWiseFee))
            fees = result.scalars().all()
            
            print(f"📊 Gefundene BuildWise Gebühren: {len(fees)}")
            
            if fees:
                print("\n📋 Gebühren-Details:")
                for fee in fees:
                    print(f"   - Fee ID {fee.id}:")
                    print(f"     * Fee Percentage: {fee.fee_percentage}%")
                    print(f"     * Fee Amount: {fee.fee_amount} {fee.currency}")
                    print(f"     * Quote Amount: {fee.quote_amount} {fee.currency}")
                    print(f"     * Status: {fee.status}")
                    print(f"     * Created: {fee.created_at}")
                    print(f"     * Updated: {fee.updated_at}")
                    print()
            else:
                print("❌ Keine BuildWise Gebühren in der Datenbank gefunden")
            
            break
            
    except Exception as e:
        print(f"❌ Fehler beim Überprüfen der Datenbank: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_buildwise_fees()) 