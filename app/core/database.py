from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .config import settings

# Verwende SQLite für die Entwicklung
DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    future=True,
    # SQLite-Optimierungen für bessere Konkurrenz
    connect_args={
        "check_same_thread": False,
        "timeout": 60.0,
        "isolation_level": None,
        "uri": True
    },
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)


async def get_db():
    """Yield an async database session with improved error handling."""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
