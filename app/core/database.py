from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from .config import settings
import os

# Database URL from environment variable
# Render provides DATABASE_URL automatically, but we need to convert postgresql:// to postgresql+asyncpg://
def get_database_url():
    """Get database URL and convert to asyncpg if needed, and add SSL mode"""
    database_url = os.getenv("DATABASE_URL", settings.database_url)
    
    # Convert postgresql:// to postgresql+asyncpg:// for async support
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    # Add SSL mode for PostgreSQL connections if not already present
    if database_url.startswith("postgresql") and "sslmode" not in database_url:
        # Add sslmode=require for Render PostgreSQL
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"
    
    return database_url

DATABASE_URL = get_database_url()

# Determine if using PostgreSQL or SQLite
IS_POSTGRESQL = DATABASE_URL.startswith("postgresql")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Configure engine based on database type
if IS_POSTGRESQL:
    # PostgreSQL Configuration for Production
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        # PostgreSQL connection pooling optimized for multi-user
        pool_pre_ping=True,  # Check connection health before using
        pool_recycle=3600,   # Recycle connections after 1 hour
        pool_size=10,        # Base connection pool size (adjust based on instance)
        max_overflow=20,     # Additional connections under load
        pool_timeout=30,     # Wait max 30s for connection from pool
        pool_reset_on_return='commit',  # Clean state on connection return
        # PostgreSQL specific settings
        connect_args={
            "server_settings": {
                "application_name": "buildwise_app",
                "jit": "off"  # Disable JIT for better connection startup
            },
            "command_timeout": 60,
            "timeout": 10,
        }
    )
    print("[INFO] Database configured: PostgreSQL (Production Mode)")
else:
    # SQLite Configuration for Development
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        # SQLite-specific settings
        connect_args={
            "check_same_thread": False,
            "timeout": 120.0,
            "isolation_level": None,
            "uri": True
        },
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=20,
        max_overflow=30,
        pool_timeout=60,
        pool_reset_on_return='commit'
    )
    print("[INFO] Database configured: SQLite (Development Mode)")

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
    Diese Funktion sollte nur für SQLite-Datenbanken aufgerufen werden.
    """
    if not IS_SQLITE:
        print("[INFO] Skipping SQLite optimizations (using PostgreSQL)")
        return
    
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


async def check_database_connection():
    """
    Prüft die Datenbankverbindung beim Start (wichtig für PostgreSQL)
    """
    try:
        async with engine.begin() as conn:
            if IS_POSTGRESQL:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"[SUCCESS] PostgreSQL connection established: {version}")
            else:
                result = await conn.execute(text("SELECT sqlite_version()"))
                version = result.scalar()
                print(f"[SUCCESS] SQLite connection established: {version}")
        return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False
