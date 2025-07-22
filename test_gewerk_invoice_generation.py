#!/usr/bin/env python3
"""
Test-Skript für die Gewerk-Rechnung-Generierung
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.buildwise_fee_service import BuildWiseFeeService
from app.models.buildwise_fee import BuildWiseFee
from sqlalchemy import select

async def test_gewerk_invoice_generation():
    """Testet die Gewerk-Rechnung-Generierung."""
    
    print("🚀 Teste Gewerk-Rechnung-Generierung...")
    print("=" * 60)
    
    try:
        async for db in get_db():
            # Hole alle BuildWise Gebühren
            result = await db.execute(select(BuildWiseFee))
            fees = result.scalars().all()
            
            if not fees:
                print("❌ Keine BuildWise Gebühren gefunden")
                return
            
            print(f"📊 Gefundene BuildWise Gebühren: {len(fees)}")
            
            # Teste mit der ersten Gebühr
            test_fee = fees[0]
            print(f"\n🔍 Teste mit Gebühr ID {test_fee.id}:")
            print(f"   - Fee Percentage: {test_fee.fee_percentage}%")
            print(f"   - Fee Amount: {test_fee.fee_amount} EUR")
            print(f"   - Quote ID: {test_fee.quote_id}")
            print(f"   - Cost Position ID: {test_fee.cost_position_id}")
            print(f"   - Project ID: {test_fee.project_id}")
            
            # Teste Gewerk-Rechnung-Generierung
            print(f"\n📄 Generiere Gewerk-Rechnung für Gebühr {test_fee.id}...")
            
            result = await BuildWiseFeeService.generate_gewerk_invoice_and_save_document(
                db=db,
                fee_id=test_fee.id,
                current_user_id=1  # Test-Benutzer-ID
            )
            
            if result["success"]:
                print("✅ Gewerk-Rechnung erfolgreich generiert!")
                print(f"   - Dokument ID: {result['document_id']}")
                print(f"   - Dokument Pfad: {result['document_path']}")
                print(f"   - PDF Pfad: {result['pdf_path']}")
                print(f"   - Nachricht: {result['message']}")
                
                # Prüfe, ob PDF-Datei existiert
                if os.path.exists(result['pdf_path']):
                    file_size = os.path.getsize(result['pdf_path'])
                    print(f"   - PDF-Datei existiert: {file_size} Bytes")
                else:
                    print("   ⚠️ PDF-Datei nicht gefunden")
                
                # Prüfe, ob Dokument-Datei existiert
                if os.path.exists(result['document_path']):
                    file_size = os.path.getsize(result['document_path'])
                    print(f"   - Dokument-Datei existiert: {file_size} Bytes")
                else:
                    print("   ⚠️ Dokument-Datei nicht gefunden")
                    
            else:
                print(f"❌ Fehler bei der Gewerk-Rechnung-Generierung: {result['error']}")
            
            break
            
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gewerk_invoice_generation()) 