import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base
from app.core.database import get_db

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(
    bind=engine_test, expire_on_commit=False, class_=AsyncSession
)


async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop()
    yield loop


@pytest.fixture(autouse=True, scope="session")
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
