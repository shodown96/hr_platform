from typing import AsyncGenerator
import pytest_asyncio
from app.core.config import settings
from app.core.db import Base, async_get_db
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import text

# TEST ENGINE
engine = create_async_engine(
    settings.TEST_SQLALCHEMY_DATABASE_URL,
    connect_args=settings.TEST_CONNECT_ARGS,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


# CREATE SCHEMA ONCE PER SESSION
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # await conn.execute(text("DROP SCHEMA public CASCADE"))
        # await conn.execute(text("CREATE SCHEMA public"))


# DB SESSION (PER TEST)
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


# HTTP CLIENT WITH DB OVERRIDE
@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[async_get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# Configure pytest for async tests
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")
