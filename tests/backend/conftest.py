"""app.config가 import 시점에 환경변수를 읽으므로, 아래 import들보다 먼저
os.environ 기본값과 sys.path를 설정해야 한다 — 이 파일 전체에 E402(모듈
상단 이후 import) 예외를 적용한다."""
# ruff: noqa: E402
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

from app.ai.providers import (
    get_emotion_analyzer,
    get_llm_provider,
    get_prosody_analyzer,
    get_report_generator,
    get_stt_provider,
)
from app.db import AsyncSessionLocal, Base, engine
from app.main import app

from fakes import (
    FakeEmotionAnalyzer,
    FakeLLMProvider,
    FakeProsodyAnalyzer,
    FakeReportGenerator,
    FakeSTTProvider,
)


@pytest_asyncio.fixture(autouse=True)
async def _clean_db():
    """각 테스트 전, 모든 테이블을 비워 독립적인 상태로 시작 (스키마는 alembic이 이미 만들어둔 것을 재사용)."""
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
    yield


@pytest.fixture(autouse=True)
def _fake_providers():
    """aimock_u3a_trd.md AC-1: 실제 Gemini/faster-whisper 대신 Fake로 어댑터 패턴 검증."""
    fake_llm = FakeLLMProvider()
    fake_stt = FakeSTTProvider()
    app.dependency_overrides[get_llm_provider] = lambda: fake_llm
    app.dependency_overrides[get_stt_provider] = lambda: fake_stt
    yield fake_llm, fake_stt
    app.dependency_overrides.pop(get_llm_provider, None)
    app.dependency_overrides.pop(get_stt_provider, None)


@pytest.fixture(autouse=True)
def _fake_report_generator():
    """aimock_u4_trd.md AC-2: 실제 Gemini 대신 Fake로 리포트 생성 오케스트레이션 검증."""
    fake_report = FakeReportGenerator()
    app.dependency_overrides[get_report_generator] = lambda: fake_report
    yield fake_report
    app.dependency_overrides.pop(get_report_generator, None)


@pytest.fixture(autouse=True)
def _fake_emotion_prosody_analyzers():
    """aimock_u3b_trd.md — 실제 DeepFace/librosa 모델 로딩 없이 고정값으로 검증."""
    fake_emotion = FakeEmotionAnalyzer()
    fake_prosody = FakeProsodyAnalyzer()
    app.dependency_overrides[get_emotion_analyzer] = lambda: fake_emotion
    app.dependency_overrides[get_prosody_analyzer] = lambda: fake_prosody
    yield fake_emotion, fake_prosody
    app.dependency_overrides.pop(get_emotion_analyzer, None)
    app.dependency_overrides.pop(get_prosody_analyzer, None)


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
