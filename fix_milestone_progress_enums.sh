#!/bin/bash
# Skript zur Behebung von Enum-Inkonsistenzen in der Datenbank
# Kann aus dem Backend-Verzeichnis (buildwise-api) ausgeführt werden

echo "🔧 Starte Enum-Korrektur für milestone_progress und quotes..."

# Verwende die PostgreSQL-Verbindung aus den Umgebungsvariablen
python3 << 'EOF'
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def fix_enum_inconsistencies():
    """Korrigiert Enum-Inkonsistenzen in der Datenbank"""
    
    # Hole DATABASE_URL aus Umgebungsvariablen
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL nicht gesetzt!")
        print("Bitte setze die DATABASE_URL Umgebungsvariable:")
        print("export DATABASE_URL='postgresql+asyncpg://user:password@host:port/database'")
        return False
    
    # Konvertiere postgresql:// zu postgresql+asyncpg://
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    elif database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    
    print(f"🔗 Verbinde mit Datenbank...")
    
    try:
        # Erstelle Engine
        engine = create_async_engine(database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            print("\n📊 Überprüfe und korrigiere Enum-Werte...")
            
            # 1. Korrigiere quote_status in quotes Tabelle
            print("\n1️⃣  Korrigiere quote_status Enum...")
            
            result1 = await session.execute(text("UPDATE quotes SET status = 'accepted' WHERE status = 'ACCEPTED'"))
            print(f"   ✅ Updated {result1.rowcount} quotes: ACCEPTED -> accepted")
            
            result2 = await session.execute(text("UPDATE quotes SET status = 'pending' WHERE status = 'PENDING'"))
            print(f"   ✅ Updated {result2.rowcount} quotes: PENDING -> pending")
            
            result3 = await session.execute(text("UPDATE quotes SET status = 'rejected' WHERE status = 'REJECTED'"))
            print(f"   ✅ Updated {result3.rowcount} quotes: REJECTED -> rejected")
            
            result4 = await session.execute(text("UPDATE quotes SET status = 'withdrawn' WHERE status = 'WITHDRAWN'"))
            print(f"   ✅ Updated {result4.rowcount} quotes: WITHDRAWN -> withdrawn")
            
            result5 = await session.execute(text("UPDATE quotes SET status = 'expired' WHERE status = 'EXPIRED'"))
            print(f"   ✅ Updated {result5.rowcount} quotes: EXPIRED -> expired")
            
            result6 = await session.execute(text("UPDATE quotes SET status = 'submitted' WHERE status = 'SUBMITTED'"))
            print(f"   ✅ Updated {result6.rowcount} quotes: SUBMITTED -> submitted")
            
            result7 = await session.execute(text("UPDATE quotes SET status = 'draft' WHERE status = 'DRAFT'"))
            print(f"   ✅ Updated {result7.rowcount} quotes: DRAFT -> draft")
            
            # 2. Korrigiere milestone_progress Enum-Werte (falls Tabelle existiert)
            print("\n2️⃣  Korrigiere milestone_progress Enums...")
            
            try:
                # update_type Enum
                result8 = await session.execute(text("UPDATE milestone_progress SET update_type = 'comment' WHERE update_type = 'COMMENT'"))
                print(f"   ✅ Updated {result8.rowcount} milestone_progress: COMMENT -> comment")
                
                result9 = await session.execute(text("UPDATE milestone_progress SET update_type = 'completion' WHERE update_type = 'COMPLETION'"))
                print(f"   ✅ Updated {result9.rowcount} milestone_progress: COMPLETION -> completion")
                
                result10 = await session.execute(text("UPDATE milestone_progress SET update_type = 'revision' WHERE update_type = 'REVISION'"))
                print(f"   ✅ Updated {result10.rowcount} milestone_progress: REVISION -> revision")
                
                result11 = await session.execute(text("UPDATE milestone_progress SET update_type = 'defect' WHERE update_type = 'DEFECT'"))
                print(f"   ✅ Updated {result11.rowcount} milestone_progress: DEFECT -> defect")
                
                result12 = await session.execute(text("UPDATE milestone_progress SET update_type = 'status_change' WHERE update_type = 'STATUS_CHANGE'"))
                print(f"   ✅ Updated {result12.rowcount} milestone_progress: STATUS_CHANGE -> status_change")
                
                # defect_severity Enum
                result13 = await session.execute(text("UPDATE milestone_progress SET defect_severity = 'minor' WHERE defect_severity = 'MINOR'"))
                print(f"   ✅ Updated {result13.rowcount} milestone_progress: MINOR -> minor")
                
                result14 = await session.execute(text("UPDATE milestone_progress SET defect_severity = 'major' WHERE defect_severity = 'MAJOR'"))
                print(f"   ✅ Updated {result14.rowcount} milestone_progress: MAJOR -> major")
                
                result15 = await session.execute(text("UPDATE milestone_progress SET defect_severity = 'critical' WHERE defect_severity = 'CRITICAL'"))
                print(f"   ✅ Updated {result15.rowcount} milestone_progress: CRITICAL -> critical")
                
            except Exception as e:
                print(f"   ⚠️  Warnung beim Aktualisieren von milestone_progress: {e}")
                print("   (Tabelle existiert möglicherweise nicht oder ist leer)")
            
            # 3. Korrigiere milestones completion_status (falls nötig)
            print("\n3️⃣  Korrigiere milestones completion_status...")
            
            try:
                result16 = await session.execute(text("UPDATE milestones SET completion_status = 'in_progress' WHERE completion_status = 'IN_PROGRESS'"))
                print(f"   ✅ Updated {result16.rowcount} milestones: IN_PROGRESS -> in_progress")
                
                result17 = await session.execute(text("UPDATE milestones SET completion_status = 'completion_requested' WHERE completion_status = 'COMPLETION_REQUESTED'"))
                print(f"   ✅ Updated {result17.rowcount} milestones: COMPLETION_REQUESTED -> completion_requested")
                
                result18 = await session.execute(text("UPDATE milestones SET completion_status = 'under_review' WHERE completion_status = 'UNDER_REVIEW'"))
                print(f"   ✅ Updated {result18.rowcount} milestones: UNDER_REVIEW -> under_review")
                
                result19 = await session.execute(text("UPDATE milestones SET completion_status = 'completed' WHERE completion_status = 'COMPLETED'"))
                print(f"   ✅ Updated {result19.rowcount} milestones: COMPLETED -> completed")
                
                result20 = await session.execute(text("UPDATE milestones SET completion_status = 'completed_with_defects' WHERE completion_status = 'COMPLETED_WITH_DEFECTS'"))
                print(f"   ✅ Updated {result20.rowcount} milestones: COMPLETED_WITH_DEFECTS -> completed_with_defects")
                
            except Exception as e:
                print(f"   ⚠️  Warnung beim Aktualisieren von milestones: {e}")
            
            # Commit aller Änderungen
            await session.commit()
            print("\n✅ Alle Änderungen wurden erfolgreich in die Datenbank übernommen!")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False

# Führe die Korrektur aus
if __name__ == "__main__":
    success = asyncio.run(fix_enum_inconsistencies())
    if success:
        print("\n🎉 Enum-Korrektur erfolgreich abgeschlossen!")
        exit(0)
    else:
        print("\n💥 Enum-Korrektur fehlgeschlagen!")
        exit(1)
EOF

