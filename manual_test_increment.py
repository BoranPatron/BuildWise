#!/usr/bin/env python3
"""
Manueller Test für Milestone-Completion-Service
Inkrementiert completed_offers_count für ein bestehendes abgeschlossenes Milestone
"""
import asyncio
import sys
import os
from sqlalchemy import text
from app.core.database import engine
from app.services.milestone_completion_service import MilestoneCompletionService

async def manual_test_increment():
    """Manueller Test der Inkrementierung"""
    print("\n" + "="*60)
    print("MANUELLER TEST: completed_offers_count INKREMENTIERUNG")
    print("="*60 + "\n")
    
    try:
        # Verwende async session für den Service
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            
            # 1. Zeige aktuelle Werte VOR der Inkrementierung
            print("[INFO] Werte VOR der Inkrementierung:")
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT id, first_name, last_name, completed_offers_count 
                    FROM users 
                    WHERE user_role = 'DIENSTLEISTER'
                """))
                users_before = result.fetchall()
                
                for user in users_before:
                    print(f"  - ID: {user[0]}, Name: {user[1]} {user[2]}, Completed Offers: {user[3] or 0}")
            
            print()
            
            # 2. Finde ein abgeschlossenes Milestone
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT id, title, completion_status 
                    FROM milestones 
                    WHERE completion_status = 'completed'
                    LIMIT 1
                """))
                milestone = result.fetchone()
                
                if not milestone:
                    print("[WARNING] Kein abgeschlossenes Milestone gefunden!")
                    return False
                
                milestone_id = milestone[0]
                milestone_title = milestone[1]
                print(f"[INFO] Gefundenes abgeschlossenes Milestone: ID {milestone_id}, Titel: '{milestone_title}'")
            
            print()
            
            # 3. Führe die Inkrementierung durch
            print("[INFO] Führe Inkrementierung durch...")
            success = await MilestoneCompletionService.increment_completed_offers_count(session, milestone_id)
            
            if success:
                print(f"[SUCCESS] Inkrementierung für Milestone {milestone_id} erfolgreich!")
            else:
                print(f"[ERROR] Inkrementierung für Milestone {milestone_id} fehlgeschlagen!")
                return False
            
            print()
            
            # 4. Zeige aktuelle Werte NACH der Inkrementierung
            print("[INFO] Werte NACH der Inkrementierung:")
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT id, first_name, last_name, completed_offers_count 
                    FROM users 
                    WHERE user_role = 'DIENSTLEISTER'
                """))
                users_after = result.fetchall()
                
                for user in users_after:
                    print(f"  - ID: {user[0]}, Name: {user[1]} {user[2]}, Completed Offers: {user[3] or 0}")
            
            print()
            
            # 5. Zeige Vergleich
            print("[INFO] Vergleich:")
            for user_before, user_after in zip(users_before, users_after):
                before_count = user_before[3] or 0
                after_count = user_after[3] or 0
                increment = after_count - before_count
                print(f"  - {user_before[1]} {user_before[2]}: {before_count} -> {after_count} (+{increment})")
            
            print()
            print("[SUCCESS] Manueller Test erfolgreich abgeschlossen!")
            return True
            
    except Exception as e:
        print(f"[ERROR] Fehler beim manuellen Test: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  BUILDWISE - MANUELLER TEST")
    print("  completed_offers_count Inkrementierung")
    print("="*60)
    
    success = asyncio.run(manual_test_increment())
    
    if success:
        print("\n" + "="*60)
        print("[ERFOLG] MANUELLER TEST ERFOLGREICH")
        print("="*60)
        print("\n[INFO] Die Logik funktioniert korrekt!")
        print("   completed_offers_count wurde erfolgreich inkrementiert.\n")
    else:
        print("\n" + "="*60)
        print("[FEHLER] MANUELLER TEST FEHLGESCHLAGEN")
        print("="*60)
        print("\n[WARNUNG] Bitte prüfen Sie die Fehlermeldungen oben.\n")
