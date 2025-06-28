from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from .config import get_settings

settings = get_settings()

# Verwende SQLite für die Entwicklung
DATABASE_URL = "sqlite+aiosqlite:///./buildwise.db"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """Yield an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
