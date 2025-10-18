from logging.config import fileConfig
import sys
import os
from sqlalchemy import pool, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import asyncio

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Get database URL from environment or settings
def get_database_url():
    """Get database URL from environment variable or settings and add SSL for PostgreSQL"""
    database_url = os.getenv("DATABASE_URL", settings.database_url)
    
    # Add SSL mode for PostgreSQL connections if not already present
    if database_url.startswith("postgresql") and "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"
    
    # For migrations, we need sync URL
    # Convert postgresql+asyncpg:// to postgresql:// for Alembic
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif database_url.startswith("sqlite+aiosqlite://"):
        database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    
    return database_url

DATABASE_URL = get_database_url()
print(f"[INFO] Alembic using database: {DATABASE_URL[:80]}...")
print(f"[DEBUG] Full DATABASE_URL contains sslmode: {'sslmode' in DATABASE_URL}")


def run_migrations_offline() -> None:
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = context.config.attributes.get("connection")
    if connectable is None:
        from sqlalchemy import create_engine
        connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,  # Enable type comparison for migrations
            compare_server_default=True  # Enable default value comparison
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
