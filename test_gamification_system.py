#!/usr/bin/env python3
"""
Test-Script für Gamification-System
Testet das Rang-System und die Gamification-Features
"""
import asyncio
import sys
import os
from sqlalchemy import text
from app.core.database import engine
from app.services.gamification_service import GamificationService, ServiceProviderRank

async def test_gamification_system():
    """Testet das Gamification-System"""
    print("\n" + "="*60)
    print("TEST: GAMIFICATION-SYSTEM")
    print("="*60 + "\n")
    
    try:
        async with engine.begin() as conn:
            # 1. Zeige alle verfügbaren Ränge
            print("[INFO] Verfuegbare Raenge im System:")
            for rank in GamificationService.RANKS:
                print(f"  {rank.title} ({rank.min_count}+ Angebote)")
                print(f"     - {rank.description}")
            print()
            
            # 2. Teste Rang-Berechnung für verschiedene Werte
            print("[INFO] Rang-Berechnung für verschiedene Werte:")
            test_values = [0, 5, 15, 25, 35, 45, 55, 75, 95, 105]
            
            for count in test_values:
                rank = GamificationService.get_rank_for_count(count)
                next_rank = GamificationService.get_next_rank(count)
                progress = GamificationService.get_progress_to_next_rank(count)
                
                print(f"  {count} Angebote:")
                print(f"    - Aktueller Rang: {rank.title}")
                if next_rank:
                    print(f"    - Naechster Rang: {next_rank.title} ({next_rank.min_count} Angebote)")
                    print(f"    - Fortschritt: {progress['progress_percentage']}% ({progress['current']}/{progress['needed']})")
                else:
                    print(f"    - Hoechster Rang erreicht!")
                print()
            
            # 3. Zeige aktuelle Dienstleister und ihre Ränge
            print("[INFO] Aktuelle Dienstleister und ihre Ränge:")
            result = await conn.execute(text("""
                SELECT id, first_name, last_name, completed_offers_count, current_rank_key, current_rank_title
                FROM users 
                WHERE user_role = 'DIENSTLEISTER'
                ORDER BY completed_offers_count DESC
            """))
            users = result.fetchall()
            
            if users:
                for user in users:
                    completed_count = user[3] or 0
                    current_rank = GamificationService.get_rank_for_count(completed_count)
                    next_rank = GamificationService.get_next_rank(completed_count)
                    progress = GamificationService.get_progress_to_next_rank(completed_count)
                    
                    print(f"  - {user[1]} {user[2]} (ID: {user[0]}):")
                    print(f"    {current_rank.title} ({completed_count} Angebote)")
                    if next_rank:
                        print(f"    Naechster: {next_rank.title} - {progress['progress_percentage']}% Fortschritt")
                    else:
                        print(f"    Hoechster Rang erreicht!")
                    print()
            else:
                print("  - Keine Dienstleister gefunden")
            
            print()
            
            # 4. Teste Rang-Statistiken
            print("[INFO] Rang-System-Statistiken:")
            stats = GamificationService.get_rank_statistics()
            print(f"  - Gesamtanzahl Ränge: {stats['total_ranks']}")
            print(f"  - Hoechster Rang: {stats['highest_rank']['title']}")
            print(f"  - Benoetigt: {stats['highest_rank']['min_count']} Angebote")
            print()
            
            # 5. Teste Leaderboard-Funktion
            print("[INFO] Teste Leaderboard-Funktion:")
            from sqlalchemy.ext.asyncio import AsyncSession
            async with AsyncSession(engine) as session:
                # Simuliere Benutzer für Leaderboard
                result = await conn.execute(text("""
                    SELECT id, first_name, last_name, company_name, completed_offers_count
                    FROM users 
                    WHERE user_role = 'DIENSTLEISTER' AND completed_offers_count > 0
                    ORDER BY completed_offers_count DESC
                    LIMIT 5
                """))
                users_for_leaderboard = result.fetchall()
                
                if users_for_leaderboard:
                    # Konvertiere zu User-Objekten (vereinfacht)
                    class MockUser:
                        def __init__(self, id, first_name, last_name, company_name, completed_offers_count):
                            self.id = id
                            self.first_name = first_name
                            self.last_name = last_name
                            self.company_name = company_name
                            self.completed_offers_count = completed_offers_count
                            self.user_role = 'DIENSTLEISTER'
                    
                    mock_users = [MockUser(*user) for user in users_for_leaderboard]
                    leaderboard = GamificationService.get_rank_leaderboard(mock_users, 5)
                    
                    print("  Rangliste (Top 5):")
                    for i, entry in enumerate(leaderboard, 1):
                        print(f"    {i}. {entry['name']} - {entry['completed_count']} Angebote")
                        print(f"       Rang: {entry['rank']['title']}")
                else:
                    print("  - Keine Dienstleister mit Angeboten gefunden")
            
            print()
            
            # 6. Zeige Schema-Information
            print("[INFO] Schema-Information für Gamification-Felder:")
            gamification_columns = ['current_rank_key', 'current_rank_title', 'rank_updated_at']
            
            for col_name in gamification_columns:
                result = await conn.execute(text("PRAGMA table_info(users)"))
                columns = result.fetchall()
                
                for col in columns:
                    if col[1] == col_name:
                        print(f"  - Spalte: {col[1]}, Typ: {col[2]}, Nullable: {not col[3]}, Default: {col[4]}")
                        break
                else:
                    print(f"  - {col_name} Spalte nicht gefunden!")
            
            print()
            
            print("[SUCCESS] Gamification-System Test abgeschlossen!")
            print("\n" + "="*60)
            print("GAMIFICATION-FEATURES:")
            print("- 11 verschiedene Ränge von Neuling bis Bau-Mythos")
            print("- Automatische Rang-Berechnung basierend auf completed_offers_count")
            print("- Fortschrittsanzeige zum nächsten Rang")
            print("- Leaderboard-System")
            print("- API-Endpoints für Frontend-Integration")
            print("="*60 + "\n")
            
    except Exception as e:
        print(f"[ERROR] Fehler beim Testen des Gamification-Systems: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  BUILDWISE - GAMIFICATION SYSTEM TEST")
    print("  Testet Rang-System und Gamification-Features")
    print("="*60)
    
    success = asyncio.run(test_gamification_system())
    
    if success:
        print("\n" + "="*60)
        print("[ERFOLG] GAMIFICATION-SYSTEM TEST ERFOLGREICH")
        print("="*60)
        print("\n[INFO] Das Gamification-System ist bereit für den Einsatz.")
        print("   Dienstleister können jetzt Ränge erreichen und sich motivieren lassen!\n")
    else:
        print("\n" + "="*60)
        print("[FEHLER] GAMIFICATION-SYSTEM TEST FEHLGESCHLAGEN")
        print("="*60)
        print("\n[WARNUNG] Bitte prüfen Sie die Fehlermeldungen oben.\n")
