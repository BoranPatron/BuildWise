import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from .config import get_settings

settings = get_settings()

# SQLite-spezifische Konfiguration für bessere Performance und Lock-Handling
SQLITE_CONFIG = {
    "check_same_thread": False,
    "timeout": 30.0,  # Timeout für Lock-Waiting
    "isolation_level": None,  # Autocommit-Modus
}

# PostgreSQL-spezifische Konfiguration
POSTGRESQL_CONFIG = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "pool_size": 10,
    "max_overflow": 20
}

# Erstelle Engine basierend auf Database-Typ
if "sqlite" in settings.database_url.lower():
    # SQLite Engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,  # SQL-Logging deaktivieren für Performance
        poolclass=StaticPool,  # Statischer Pool für SQLite
        connect_args=SQLITE_CONFIG,
        pool_pre_ping=True,  # Connection-Health-Check
        pool_recycle=3600,  # Recycle Connections nach 1 Stunde
    )
else:
    # PostgreSQL Engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        **POSTGRESQL_CONFIG
    )

# Session-Factory mit optimierten Einstellungen
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Verhindert Lazy Loading Probleme
    autocommit=False,
    autoflush=False,
)

# Base-Klasse für Models
Base = declarative_base()

# Metadata für Schema-Management
metadata = MetaData()

async def get_db():
    """Dependency für Datenbank-Sessions mit Error-Handling"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"❌ Database Error: {e}")
            raise
        finally:
            await session.close()

# Hilfsfunktion für Database-Health-Check
async def check_database_health():
    """Prüft die Datenbankverbindung und gibt Status zurück"""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database error: {e}"}

# Hilfsfunktion für Database-Reset (bei Lock-Problemen)
async def reset_database_connection():
    """Reset der Datenbankverbindung bei Lock-Problemen"""
    try:
        await engine.dispose()
        print("✅ Database connection reset successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to reset database connection: {e}")
        return False
