import os
import sys
from pathlib import Path

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://aimock:aimock_dev_only@localhost:55432/aimock"
)
os.environ.setdefault("JWT_SECRET", "test-only-secret")
os.environ.setdefault("MEDIA_ENCRYPTION_KEY", "k86IFwa9sPVr0re2TATgKNzRs_yuQInAWQzrApfYD70=")
os.environ.setdefault("MEDIA_STORAGE_DIR", "test_uploads")

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "src" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db import AsyncSessionLocal, Base, engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _clean_db():
    """각 테스트 전, 모든 테이블을 비워 독립적인 상태로 시작 (스키마는 alembic이 이미 만들어둔 것을 재사용)."""
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def anyio_backend():
    return "asyncio"
