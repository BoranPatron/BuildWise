from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from .config import settings

# Verwende SQLite für die Entwicklung
DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    future=True,
    # SQLite-Optimierungen für bessere Konkurrenz und Performance
    connect_args={
        "check_same_thread": False,
        "timeout": 120.0,  # Erhöht auf 120 Sekunden
        "isolation_level": None,
        "uri": True
    },
    pool_pre_ping=True,
    pool_recycle=1800,  # Reduziert auf 30 Minuten
    pool_size=20,  # Erhöht auf 20 Verbindungen
    max_overflow=30,  # Erhöht auf 30 zusätzliche Verbindungen
    pool_timeout=60,  # 60 Sekunden Timeout für Pool-Verbindungen
    pool_reset_on_return='commit'  # Automatisches Commit bei Rückgabe
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)


async def get_db():
    """Yield an async database session with improved error handling and timeout management."""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        print(f"[ERROR] Datenbankfehler: {e}")
        await session.rollback()
        raise e
    finally:
        await session.close()


async def optimize_sqlite_connection():
    """
    Optimiere SQLite-Verbindung einmalig beim Start der Anwendung.
    Diese Funktion sollte beim App-Start aufgerufen werden.
    """
    try:
        async with engine.begin() as conn:
            # SQLite-Optimierungen auf Connection-Level
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))
            await conn.execute(text("PRAGMA cache_size=-64000"))
            await conn.execute(text("PRAGMA temp_store=MEMORY"))
            await conn.execute(text("PRAGMA mmap_size=268435456"))
            await conn.execute(text("PRAGMA page_size=4096"))
            await conn.execute(text("PRAGMA auto_vacuum=INCREMENTAL"))
            # Zusätzliche Optimierungen für weniger Locks
            await conn.execute(text("PRAGMA busy_timeout=30000"))  # 30 Sekunden Timeout
            await conn.execute(text("PRAGMA wal_autocheckpoint=1000"))  # WAL Checkpoint alle 1000 Pages
            await conn.execute(text("PRAGMA optimize"))  # Optimiere Statistiken
            await conn.commit()
            print("[SUCCESS] SQLite-Optimierungen erfolgreich angewendet")
    except Exception as e:
        print(f"[WARNING] SQLite-Optimierungen konnten nicht angewendet werden: {e}")
        # Fahre trotz Fehler fort - die Anwendung sollte auch ohne Optimierungen funktionieren
