#!/usr/bin/env python3
"""
Automatische PDF-Generierung für BuildWise-Gebühren
Generiert PDFs für alle Gebühren, die noch kein PDF haben
"""

import asyncio
import os
import sys
from datetime import datetime

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.buildwise_fee import BuildWiseFee
from app.models.project import Project
from app.models.quote import Quote
from app.models.cost_position import CostPosition
from app.services.buildwise_fee_service import BuildWiseFeeService

async def fix_missing_pdfs():
    """Generiert automatisch PDFs für alle BuildWise-Gebühren ohne PDF"""
    
    print("🔧 Starte automatische PDF-Generierung für BuildWise-Gebühren...")
    
    # Datenbankverbindung
    DATABASE_URL = "sqlite+aiosqlite:///buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # Hole alle Gebühren ohne PDF
            query = select(BuildWiseFee).where(
                (BuildWiseFee.invoice_pdf_generated == False) | 
                (BuildWiseFee.invoice_pdf_generated.is_(None))
            )
            result = await db.execute(query)
            fees_without_pdf = result.scalars().all()
            
            print(f"📊 Gefundene Gebühren ohne PDF: {len(fees_without_pdf)}")
            
            if len(fees_without_pdf) == 0:
                print("✅ Alle Gebühren haben bereits PDFs!")
                return
            
            # Generiere PDFs für jede Gebühr
            success_count = 0
            error_count = 0
            
            for fee in fees_without_pdf:
                print(f"\n🔍 Generiere PDF für Gebühr ID {fee.id}...")
                print(f"  Projekt ID: {fee.project_id}")
                print(f"  Betrag: {fee.fee_amount} €")
                print(f"  Status: {fee.status}")
                
                try:
                    # Prüfe ob alle notwendigen Daten vorhanden sind
                    project_query = select(Project).where(Project.id == fee.project_id)
                    project_result = await db.execute(project_query)
                    project = project_result.scalar_one_or_none()
                    
                    quote_query = select(Quote).where(Quote.id == fee.quote_id)
                    quote_result = await db.execute(quote_query)
                    quote = quote_result.scalar_one_or_none()
                    
                    cost_position_query = select(CostPosition).where(CostPosition.id == fee.cost_position_id)
                    cost_position_result = await db.execute(cost_position_query)
                    cost_position = cost_position_result.scalar_one_or_none()
                    
                    if not project:
                        print(f"  ❌ Projekt {fee.project_id} nicht gefunden")
                        error_count += 1
                        continue
                    
                    if not quote:
                        print(f"  ❌ Quote {fee.quote_id} nicht gefunden")
                        error_count += 1
                        continue
                    
                    if not cost_position:
                        print(f"  ❌ CostPosition {fee.cost_position_id} nicht gefunden")
                        error_count += 1
                        continue
                    
                    # Generiere PDF
                    success = await BuildWiseFeeService.generate_invoice(db, fee.id)
                    
                    if success:
                        print(f"  ✅ PDF erfolgreich generiert")
                        success_count += 1
                    else:
                        print(f"  ❌ PDF-Generierung fehlgeschlagen")
                        error_count += 1
                        
                except Exception as e:
                    print(f"  ❌ Fehler bei Gebühr {fee.id}: {e}")
                    error_count += 1
            
            print(f"\n📊 Zusammenfassung:")
            print(f"  ✅ Erfolgreich generiert: {success_count}")
            print(f"  ❌ Fehler: {error_count}")
            print(f"  📄 Gesamt: {len(fees_without_pdf)}")
            
    except Exception as e:
        print(f"❌ Fehler beim Generieren der PDFs: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()

async def check_pdf_status():
    """Prüft den PDF-Status aller BuildWise-Gebühren"""
    
    print("🔍 Prüfe PDF-Status aller BuildWise-Gebühren...")
    
    # Datenbankverbindung
    DATABASE_URL = "sqlite+aiosqlite:///buildwise.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # Hole alle Gebühren
            query = select(BuildWiseFee).order_by(BuildWiseFee.id)
            result = await db.execute(query)
            all_fees = result.scalars().all()
            
            print(f"📊 Gesamtanzahl Gebühren: {len(all_fees)}")
            
            with_pdf = 0
            without_pdf = 0
            
            for fee in all_fees:
                if fee.invoice_pdf_generated:
                    with_pdf += 1
                    status = "✅"
                else:
                    without_pdf += 1
                    status = "❌"
                
                print(f"  {status} Gebühr ID {fee.id}: PDF {'vorhanden' if fee.invoice_pdf_generated else 'fehlt'}")
            
            print(f"\n📊 PDF-Status:")
            print(f"  ✅ Mit PDF: {with_pdf}")
            print(f"  ❌ Ohne PDF: {without_pdf}")
            print(f"  📄 Gesamt: {len(all_fees)}")
            
    except Exception as e:
        print(f"❌ Fehler beim Prüfen des PDF-Status: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()

async def main():
    """Hauptfunktion"""
    
    print("🚀 BuildWise-Gebühren PDF-Fix Tool")
    print("=" * 50)
    
    # Prüfe zuerst den aktuellen Status
    await check_pdf_status()
    
    print("\n" + "=" * 50)
    
    # Frage Benutzer, ob PDFs generiert werden sollen
    response = input("\nMöchten Sie PDFs für alle Gebühren ohne PDF generieren? (j/n): ")
    
    if response.lower() in ['j', 'ja', 'y', 'yes']:
        await fix_missing_pdfs()
        
        print("\n" + "=" * 50)
        
        # Prüfe den Status nach der Generierung
        await check_pdf_status()
    else:
        print("❌ PDF-Generierung abgebrochen")

if __name__ == "__main__":
    asyncio.run(main()) 