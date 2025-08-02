"""
Migration zum Hinzufügen von Baufortschrittsdokumentation und Bewertungssystem
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Bestimme die Datenbank-URL basierend auf der Umgebung
if os.path.exists('buildwise.db'):
    DATABASE_URL = "sqlite+aiosqlite:///buildwise.db"
else:
    DATABASE_URL = "sqlite+aiosqlite:///BuildWise/buildwise.db"

print(f"Verwende Datenbank: {DATABASE_URL}")

async def run_migration():
    # Erstelle Engine und Session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            print("Starte Migration für Baufortschrittsdokumentation und Bewertungssystem...")
            
            # 1. Erstelle milestone_progress Tabelle
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS milestone_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    milestone_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    update_type VARCHAR(50) NOT NULL DEFAULT 'comment',
                    message TEXT NOT NULL,
                    progress_percentage INTEGER,
                    attachments TEXT,  -- JSON Array
                    parent_id INTEGER,
                    defect_severity VARCHAR(50),
                    defect_resolved BOOLEAN DEFAULT 0,
                    revision_deadline DATETIME,
                    revision_completed BOOLEAN DEFAULT 0,
                    is_internal BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_id) REFERENCES milestone_progress(id)
                )
            """))
            
            # 2. Erstelle service_provider_ratings Tabelle
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS service_provider_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bautraeger_id INTEGER NOT NULL,
                    service_provider_id INTEGER NOT NULL,
                    project_id INTEGER NOT NULL,
                    milestone_id INTEGER NOT NULL,
                    quote_id INTEGER,
                    quality_rating FLOAT NOT NULL,
                    timeliness_rating FLOAT NOT NULL,
                    communication_rating FLOAT NOT NULL,
                    value_rating FLOAT NOT NULL,
                    overall_rating FLOAT NOT NULL,
                    comment TEXT,
                    is_public INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bautraeger_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (service_provider_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE CASCADE,
                    FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
                    UNIQUE (bautraeger_id, service_provider_id, milestone_id)
                )
            """))
            
            # 3. Füge neue Felder zu quotes hinzu (falls nicht vorhanden)
            # Prüfe ob Spalten existieren
            result = await session.execute(text("PRAGMA table_info(quotes)"))
            columns = [row[1] for row in result]
            
            # contact_released Feld
            if 'contact_released' not in columns:
                await session.execute(text("""
                    ALTER TABLE quotes ADD COLUMN contact_released BOOLEAN DEFAULT 0
                """))
                print("✅ Spalte 'contact_released' zu quotes hinzugefügt")
            
            # contact_released_at Feld
            if 'contact_released_at' not in columns:
                await session.execute(text("""
                    ALTER TABLE quotes ADD COLUMN contact_released_at DATETIME
                """))
                print("✅ Spalte 'contact_released_at' zu quotes hinzugefügt")
            
            # 4. Füge neue Felder zu milestones hinzu für Invoice-Handling
            result = await session.execute(text("PRAGMA table_info(milestones)"))
            columns = [row[1] for row in result]
            
            # invoice_amount Feld
            if 'invoice_amount' not in columns:
                await session.execute(text("""
                    ALTER TABLE milestones ADD COLUMN invoice_amount FLOAT
                """))
                print("✅ Spalte 'invoice_amount' zu milestones hinzugefügt")
            
            # invoice_due_date Feld
            if 'invoice_due_date' not in columns:
                await session.execute(text("""
                    ALTER TABLE milestones ADD COLUMN invoice_due_date DATE
                """))
                print("✅ Spalte 'invoice_due_date' zu milestones hinzugefügt")
            
            # invoice_pdf_url Feld
            if 'invoice_pdf_url' not in columns:
                await session.execute(text("""
                    ALTER TABLE milestones ADD COLUMN invoice_pdf_url VARCHAR(500)
                """))
                print("✅ Spalte 'invoice_pdf_url' zu milestones hinzugefügt")
                
            # 5. Erstelle Indices für bessere Performance
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_milestone_progress_milestone 
                ON milestone_progress(milestone_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_milestone_progress_user 
                ON milestone_progress(user_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_milestone_progress_parent 
                ON milestone_progress(parent_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_service_provider_ratings_service_provider 
                ON service_provider_ratings(service_provider_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_service_provider_ratings_project 
                ON service_provider_ratings(project_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_service_provider_ratings_milestone 
                ON service_provider_ratings(milestone_id)
            """))
            
            await session.commit()
            print("✅ Migration erfolgreich abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler bei der Migration: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())