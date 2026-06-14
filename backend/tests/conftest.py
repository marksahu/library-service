"""
tests/conftest.py

Shared fixtures for the test suite.
Uses an async SQLite in-memory database so tests run without PostgreSQL.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db.session import Base, get_db
from app.main import app

# ─── In-memory SQLite engine ──────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine):
    """Yields a transactional session that is rolled back after each test."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await session.begin_nested()   # savepoint
        yield session
        await session.rollback()       # always roll back → isolated tests


@pytest_asyncio.fixture
async def client(db):
    """AsyncClient wired to the FastAPI app with the test DB session."""
    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ─── Convenience factories ────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def book(client):
    r = await client.post("/books", json={
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": "9780132350884",
        "genre": "Technology",
        "year": 2008,
        "copies": 2,
    })
    assert r.status_code == 201
    return r.json()


@pytest_asyncio.fixture
async def member(client):
    r = await client.post("/members", json={
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "555-0101",
        "address": "12 Maple St",
    })
    assert r.status_code == 201
    return r.json()


@pytest_asyncio.fixture
async def loan(client, book, member):
    r = await client.post("/loans/borrow", json={
        "member_id": member["id"],
        "book_id":   book["id"],
        "loan_days": 14,
    })
    assert r.status_code == 201
    return r.json()
