"""Shared test fixtures for CryptoForget."""

import pytest
import pytest_asyncio
from app.db.base import Base
from app.db.session import engine
import app.models  # ensure all models registered with Base.metadata


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Ensures all SQLite database tables exist before any test runs."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
def synthetic_user_id() -> str:
    """Return a synthetic user ID for testing."""
    return "test-user-001"


@pytest.fixture
def synthetic_record_id() -> str:
    """Return a synthetic record ID for testing."""
    return "test-record-001"
