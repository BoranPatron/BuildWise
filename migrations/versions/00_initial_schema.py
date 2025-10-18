"""Initial database schema

Revision ID: 00_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '00_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all initial tables from Base.metadata"""
    
    # This migration creates ALL tables with ALL their current columns
    # This is the initial schema that reflects the current state of models
    
    # Import Base to get all models
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from app.models import Base
    from sqlalchemy import create_engine, inspect
    from app.core.config import settings
    
    # Get the current database URL
    database_url = os.getenv("DATABASE_URL", str(settings.database_url))
    
    # Convert async URLs to sync
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif database_url.startswith("sqlite+aiosqlite://"):
        database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    
    # Add SSL for PostgreSQL if needed
    if database_url.startswith("postgresql") and "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"
    
    # Create engine with proper SSL settings for PostgreSQL
    connect_args = {}
    if database_url.startswith("postgresql"):
        connect_args = {
            "sslmode": "allow",
            "connect_timeout": 10
        }
    
    engine = create_engine(database_url, connect_args=connect_args)
    
    # Only create tables that don't exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if not existing_tables:
        # Fresh database - create all tables
        print("[INFO] Creating all tables from scratch...")
        Base.metadata.create_all(bind=engine)
    else:
        # Some tables exist - create only missing ones
        print(f"[INFO] Database has {len(existing_tables)} existing tables")
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                print(f"[INFO] Creating table: {table.name}")
                table.create(bind=engine, checkfirst=True)
    
    engine.dispose()


def downgrade():
    """Drop all tables"""
    
    # Import Base to get all models
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from app.models import Base
    from sqlalchemy import create_engine
    from app.core.config import settings
    
    # Get the current database URL
    database_url = os.getenv("DATABASE_URL", str(settings.database_url))
    
    # Convert async URLs to sync
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif database_url.startswith("sqlite+aiosqlite://"):
        database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    
    # Drop all tables using SQLAlchemy metadata
    engine = create_engine(database_url)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

