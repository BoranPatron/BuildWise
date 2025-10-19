#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Script für Account-Sperre Debugging
"""
import asyncio
import sys
from datetime import date, timedelta, datetime
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.buildwise_fee import BuildWiseFee
from app.models.user import User

# Fix encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

async def check_overdue_fees():
    """Prüft überfällige Gebühren"""
    async with AsyncSessionLocal() as db:
        try:
            print("=" * 60)
            print("CHECKING OVERDUE FEES")
            print("=" * 60)
            
            # Alle Gebühren laden
            query = select(BuildWiseFee)
            result = await db.execute(query)
            fees = result.scalars().all()
            
            print(f"\nGefundene Gebuehren: {len(fees)}")
            print("-" * 60)
            
            today = date.today()
            print(f"Heute: {today.isoformat()}\n")
            
            overdue_count = 0
            
            for fee in fees:
                print(f"\nGebuehr ID: {fee.id}")
                print(f"   Rechnungsnummer: {fee.invoice_number}")
                print(f"   Dienstleister ID: {fee.service_provider_id}")
                print(f"   Status: {fee.status}")
                print(f"   Faelligkeitsdatum: {fee.due_date}")
                print(f"   Betrag: {fee.fee_amount} {fee.currency}")
                
                if fee.due_date:
                    # Konvertiere zu date object falls nötig
                    if isinstance(fee.due_date, str):
                        due_date_obj = datetime.fromisoformat(fee.due_date.replace('Z', '+00:00')).date()
                    else:
                        due_date_obj = fee.due_date
                    
                    is_overdue = due_date_obj < today
                    days_diff = (today - due_date_obj).days
                    
                    print(f"   Tage Differenz: {days_diff}")
                    print(f"   Ueberfaellig: {'JA' if is_overdue else 'NEIN'}")
                    
                    if is_overdue:
                        overdue_count += 1
                        print(f"   >>> UEBERFAELLIG SEIT {days_diff} TAGEN! <<<")
                else:
                    print(f"   Kein Faelligkeitsdatum gesetzt")
            
            print("\n" + "=" * 60)
            print(f"TOTAL UEBERFAELLIGE GEBUEHREN: {overdue_count}")
            print("=" * 60)
            
            # Prüfe User-Role
            print("\n" + "=" * 60)
            print("CHECKING USERS WITH FEES")
            print("=" * 60)
            
            service_provider_ids = set(fee.service_provider_id for fee in fees if fee.service_provider_id)
            
            for sp_id in service_provider_ids:
                user_query = select(User).where(User.id == sp_id)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()
                
                if user:
                    print(f"\nUser ID {sp_id}:")
                    print(f"   Email: {user.email}")
                    print(f"   Role: {user.user_role}")
                    
                    # Check if DIENSTLEISTER
                    is_dienstleister = False
                    if hasattr(user.user_role, 'value'):
                        is_dienstleister = user.user_role.value == 'DIENSTLEISTER'
                    else:
                        is_dienstleister = str(user.user_role) == 'DIENSTLEISTER'
                    
                    print(f"   Role ist DIENSTLEISTER: {is_dienstleister}")
                    
                    # Zähle überfällige Gebühren für diesen User
                    user_overdue = 0
                    for fee in fees:
                        if fee.service_provider_id == sp_id and fee.due_date:
                            if isinstance(fee.due_date, str):
                                due_date_obj = datetime.fromisoformat(fee.due_date.replace('Z', '+00:00')).date()
                            else:
                                due_date_obj = fee.due_date
                            
                            if due_date_obj < today:
                                user_overdue += 1
                    
                    print(f"   Ueberfaellige Gebuehren: {user_overdue}")
                    if user_overdue > 0 and is_dienstleister:
                        print(f"   >>> ACCOUNT SOLLTE GESPERRT SEIN! <<<")
                else:
                    print(f"\nUser ID {sp_id} nicht gefunden!")
            
        except Exception as e:
            print(f"Fehler: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_overdue_fees())
