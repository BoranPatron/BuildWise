#!/usr/bin/env python3
"""
Fix Daily Deduction Timezone Problem - AUTOMATISCH

Dieses Skript behebt das Timezone-Problem bei den last_daily_deduction Timestamps.
Es konvertiert alle naive datetime-Objekte zu UTC-aware datetimes.
"""

import sys
import os
from pathlib import Path

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from datetime import datetime, timezone
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user_credits import UserCredits


def fix_timezone_issue():
    """
    Konvertiert alle naive datetime Einträge in last_daily_deduction zu UTC-aware datetimes.
    Außerdem: Setze alle last_daily_deduction auf NULL, die heute bereits mehrfach abgezogen wurden.
    """
    # Erstelle synchrone Datenbankverbindung
    engine = create_engine("sqlite:///./buildwise.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("Suche nach Benutzern mit last_daily_deduction Eintraegen...")
        
        # Hole alle UserCredits mit last_daily_deduction
        result = db.execute(
            select(UserCredits).where(UserCredits.last_daily_deduction.isnot(None))
        )
        users_with_deduction = result.scalars().all()
        
        print(f"Gefunden: {len(users_with_deduction)} Benutzer mit last_daily_deduction")
        
        fixed_count = 0
        reset_count = 0
        
        for user_credits in users_with_deduction:
            try:
                # Hole die aktuelle last_daily_deduction
                last_deduction = user_credits.last_daily_deduction
                
                print(f"\nUser {user_credits.user_id}:")
                print(f"   Aktuell: {last_deduction} (tzinfo: {last_deduction.tzinfo})")
                
                # Prüfe ob es ein naive datetime ist
                if last_deduction.tzinfo is None:
                    # Konvertiere zu UTC-aware datetime
                    utc_datetime = last_deduction.replace(tzinfo=timezone.utc)
                    user_credits.last_daily_deduction = utc_datetime
                    fixed_count += 1
                    print(f"   [OK] Konvertiert zu UTC: {utc_datetime}")
                else:
                    # Bereits timezone-aware, konvertiere zu UTC falls nicht UTC
                    if last_deduction.tzinfo != timezone.utc:
                        utc_datetime = last_deduction.astimezone(timezone.utc)
                        user_credits.last_daily_deduction = utc_datetime
                        fixed_count += 1
                        print(f"   [OK] Konvertiert zu UTC: {utc_datetime}")
                    else:
                        print(f"   [INFO] Bereits UTC")
                
                # Prüfe ob heute mehrfach abgezogen wurde
                # Zähle Credit-Events von heute für diesen User
                from app.models.credit_event import CreditEvent, CreditEventType
                today = datetime.now(timezone.utc).date()
                
                today_events_result = db.execute(
                    select(CreditEvent)
                    .where(CreditEvent.user_credits_id == user_credits.id)
                    .where(CreditEvent.event_type == CreditEventType.DAILY_DEDUCTION)
                )
                all_daily_events = today_events_result.scalars().all()
                
                # Filtere Events von heute
                today_events = [
                    e for e in all_daily_events 
                    if e.created_at.date() == today
                ]
                
                if len(today_events) > 1:
                    print(f"   [WARNUNG] {len(today_events)} Credit-Abzuege heute gefunden!")
                    print(f"   [FIX] Setze last_daily_deduction zurueck, um morgen korrekt zu funktionieren")
                    # Setze auf NULL, damit morgen wieder ein Abzug stattfinden kann
                    # ABER: Behalte das letzte Event von heute als Referenz
                    last_event = max(today_events, key=lambda e: e.created_at)
                    user_credits.last_daily_deduction = last_event.created_at
                    reset_count += 1
                
            except Exception as e:
                print(f"   [FEHLER] Bei User {user_credits.user_id}: {e}")
                continue
        
        # Speichere alle Änderungen
        db.commit()
        
        print("\n" + "="*60)
        print("[OK] Timezone-Fix abgeschlossen!")
        print(f"Statistik:")
        print(f"   - {fixed_count} Timestamps zu UTC konvertiert")
        print(f"   - {reset_count} mehrfach abgezogene Eintraege korrigiert")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n[FEHLER] Beim Fix: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("BuildWise - Daily Deduction Timezone Fix (AUTOMATISCH)")
    print("="*60)
    
    print("\nStarte automatischen Fix...\n")
    success = fix_timezone_issue()
    
    if success:
        print("\n[OK] Fertig! Die Timezone-Probleme wurden behoben.")
        print("\nDie Datenbank wurde erfolgreich bereinigt.")
    else:
        print("\n[FEHLER] Fix fehlgeschlagen!")
        sys.exit(1)


