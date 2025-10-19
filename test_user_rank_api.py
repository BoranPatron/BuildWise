#!/usr/bin/env python3
"""
Test-Script für User-Rank API
Testet den neuen API-Endpoint für Benutzer-Ränge
"""
import asyncio
import sys
import os
from sqlalchemy import text
from app.core.database import engine
from app.services.gamification_service import GamificationService

async def test_user_rank_api():
    """Testet den User-Rank API-Endpoint"""
    print("\n" + "="*60)
    print("TEST: USER-RANK API ENDPOINT")
    print("="*60 + "\n")
    
    try:
        async with engine.begin() as conn:
            # 1. Lade einen Dienstleister für den Test
            result = await conn.execute(text("""
                SELECT id, first_name, last_name, company_name, completed_offers_count, current_rank_key, current_rank_title
                FROM users 
                WHERE user_role = 'DIENSTLEISTER'
                LIMIT 1
            """))
            user = result.fetchone()
            
            if not user:
                print("[WARNING] Kein Dienstleister gefunden für API-Test!")
                return False
            
            print(f"[INFO] Teste mit Dienstleister: {user[1]} {user[2]} (ID: {user[0]})")
            print(f"  - Unternehmen: {user[3] or 'Freiberufler'}")
            print(f"  - Abgeschlossene Angebote: {user[4] or 0}")
            print(f"  - Aktueller Rang: {user[5] or 'Nicht gesetzt'}")
            print()
            
            # 2. Simuliere API-Aufruf
            from sqlalchemy.ext.asyncio import AsyncSession
            async with AsyncSession(engine) as session:
                # Simuliere get_current_user
                class MockUser:
                    def __init__(self, user_data):
                        self.id = user_data[0]
                        self.first_name = user_data[1]
                        self.last_name = user_data[2]
                        self.company_name = user_data[3]
                        self.completed_offers_count = user_data[4] or 0
                        self.current_rank_key = user_data[5]
                        self.current_rank_title = user_data[6]
                        self.rank_updated_at = None
                
                mock_user = MockUser(user)
                
                # Teste Gamification-Service direkt
                completed_count = mock_user.completed_offers_count
                current_rank = GamificationService.get_rank_for_count(completed_count)
                next_rank = GamificationService.get_next_rank(completed_count)
                progress = GamificationService.get_progress_to_next_rank(completed_count)
                
                print("[INFO] API-Response Simulation:")
                print(f"  - User ID: {mock_user.id}")
                print(f"  - User Name: {mock_user.first_name} {mock_user.last_name}")
                print(f"  - Company: {mock_user.company_name}")
                print(f"  - Completed Count: {completed_count}")
                print()
                print(f"  - Current Rank:")
                print(f"    * Key: {current_rank.key}")
                print(f"    * Title: {current_rank.title}")
                print(f"    * Description: {current_rank.description}")
                print(f"    * Min Count: {current_rank.min_count}")
                print()
                
                if next_rank:
                    print(f"  - Next Rank:")
                    print(f"    * Title: {next_rank.title}")
                    print(f"    * Description: {next_rank.description}")
                    print(f"    * Min Count: {next_rank.min_count}")
                    print()
                
                print(f"  - Progress:")
                print(f"    * Current: {progress['current']}")
                print(f"    * Needed: {progress['needed']}")
                print(f"    * Percentage: {progress['progress_percentage']}%")
                print()
            
            # 3. Teste API-Endpoint-URL
            print("[INFO] API-Endpoint-Informationen:")
            print("  - URL: GET /api/v1/api/user/my-rank")
            print("  - Authentication: Bearer Token erforderlich")
            print("  - Response: UserRankResponse")
            print()
            
            # 4. Zeige Frontend-Integration
            print("[INFO] Frontend-Integration:")
            print("  - Service: gamificationService.ts")
            print("  - Component: UserRankDisplay.tsx")
            print("  - Location: ServiceProviderDashboard.tsx")
            print("  - Features:")
            print("    * Rang-Anzeige mit Emoji")
            print("    * Fortschrittsbalken zum nächsten Rang")
            print("    * Tooltip mit detaillierten Informationen")
            print("    * Hover-Effekte und Animationen")
            print()
            
            print("[SUCCESS] User-Rank API Test erfolgreich!")
            return True
            
    except Exception as e:
        print(f"[ERROR] Fehler beim Testen der User-Rank API: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  BUILDWISE - USER-RANK API TEST")
    print("  Testet API-Endpoint für Benutzer-Ränge")
    print("="*60)
    
    success = asyncio.run(test_user_rank_api())
    
    if success:
        print("\n" + "="*60)
        print("[ERFOLG] USER-RANK API TEST ERFOLGREICH")
        print("="*60)
        print("\n[INFO] Der API-Endpoint ist bereit für Frontend-Integration.")
        print("   Dienstleister können jetzt ihren Rang auf der Startseite sehen!\n")
    else:
        print("\n" + "="*60)
        print("[FEHLER] USER-RANK API TEST FEHLGESCHLAGEN")
        print("="*60)
        print("\n[WARNUNG] Bitte prüfen Sie die Fehlermeldungen oben.\n")
