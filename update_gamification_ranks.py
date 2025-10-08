#!/usr/bin/env python3
"""
Update-Script für Gamification-System
Aktualisiert Ränge für alle bestehenden Dienstleister
"""
import asyncio
import sys
import os
from sqlalchemy import text
from app.core.database import engine
from app.services.gamification_service import GamificationService

async def update_all_user_ranks():
    """Aktualisiert Ränge für alle Dienstleister"""
    print("\n" + "="*60)
    print("UPDATE: GAMIFICATION-RÄNGE FÜR ALLE DIENSTLEISTER")
    print("="*60 + "\n")
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            
            # 1. Lade alle Dienstleister
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT id, first_name, last_name, completed_offers_count, current_rank_key
                    FROM users 
                    WHERE user_role = 'DIENSTLEISTER'
                    ORDER BY completed_offers_count DESC
                """))
                users = result.fetchall()
            
            if not users:
                print("[WARNING] Keine Dienstleister gefunden!")
                return False
            
            print(f"[INFO] Gefunden: {len(users)} Dienstleister")
            print()
            
            # 2. Aktualisiere Ränge für jeden Dienstleister
            updated_count = 0
            rank_changes = 0
            
            for user in users:
                user_id = user[0]
                user_name = f"{user[1]} {user[2]}"
                completed_count = user[3] or 0
                current_rank_key = user[4]
                
                print(f"[INFO] Aktualisiere Rang für {user_name} (ID: {user_id})...")
                print(f"  - Aktuelle Angebote: {completed_count}")
                print(f"  - Aktueller Rang in DB: {current_rank_key or 'Nicht gesetzt'}")
                
                # Berechne neuen Rang
                new_rank = GamificationService.get_rank_for_count(completed_count)
                print(f"  - Berechneter Rang: {new_rank.title}")
                
                # Aktualisiere Rang
                rank_info = await GamificationService.update_user_rank(session, user_id)
                
                if rank_info:
                    updated_count += 1
                    if rank_info.get('rank_changed'):
                        rank_changes += 1
                        print(f"  - [RANG-ÄNDERUNG] {rank_info['current_rank']['title']}")
                    else:
                        print(f"  - [KEINE ÄNDERUNG] Rang bereits korrekt")
                else:
                    print(f"  - [FEHLER] Rang-Update fehlgeschlagen")
                
                print()
            
            # 3. Zeige Zusammenfassung
            print("="*60)
            print(f"[ERFOLG] Rang-Update abgeschlossen!")
            print(f"  - Dienstleister aktualisiert: {updated_count}/{len(users)}")
            print(f"  - Rang-Änderungen: {rank_changes}")
            print("="*60)
            
            # 4. Zeige aktuelle Rang-Verteilung
            print("\n[INFO] Aktuelle Rang-Verteilung:")
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT current_rank_title, COUNT(*) as count
                    FROM users 
                    WHERE user_role = 'DIENSTLEISTER' AND current_rank_title IS NOT NULL
                    GROUP BY current_rank_title
                    ORDER BY count DESC
                """))
                rank_distribution = result.fetchall()
                
                if rank_distribution:
                    for rank_title, count in rank_distribution:
                        print(f"  - {rank_title}: {count} Dienstleister")
                else:
                    print("  - Keine Rang-Verteilung verfügbar")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Fehler beim Aktualisieren der Ränge: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  BUILDWISE - GAMIFICATION RANK UPDATE")
    print("  Aktualisiert Ränge für alle Dienstleister")
    print("="*60)
    
    success = asyncio.run(update_all_user_ranks())
    
    if success:
        print("\n" + "="*60)
        print("[ERFOLG] RANG-UPDATE ERFOLGREICH")
        print("="*60)
        print("\n[INFO] Alle Dienstleister haben jetzt ihre korrekten Ränge.")
        print("   Das Gamification-System ist vollständig aktiviert!\n")
    else:
        print("\n" + "="*60)
        print("[FEHLER] RANG-UPDATE FEHLGESCHLAGEN")
        print("="*60)
        print("\n[WARNUNG] Bitte prüfen Sie die Fehlermeldungen oben.\n")
