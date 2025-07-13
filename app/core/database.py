from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .config import get_settings
import os

settings = get_settings()

# Dynamische Datenbank-URL basierend auf Environment
def get_database_url():
    # Prüfe auf PostgreSQL-URL (für Render.com)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Render.com verwendet PostgreSQL mit postgres://, aber SQLAlchemy erwartet postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    
    # Fallback: SQLite für lokale Entwicklung
    return "sqlite+aiosqlite:///./buildwise.db"

DATABASE_URL = get_database_url()

# Engine-Konfiguration basierend auf Datenbank-Typ
if DATABASE_URL.startswith("sqlite"):
    # SQLite-Konfiguration
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False, 
        future=True,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL-Konfiguration
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False, 
        future=True,
        pool_pre_ping=True,  # Für bessere Verbindungsstabilität
        pool_recycle=300     # Verbindungen nach 5 Minuten erneuern
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """Yield an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
