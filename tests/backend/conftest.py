"""app.config가 import 시점에 환경변수를 읽으므로, 아래 import들보다 먼저
os.environ 기본값과 sys.path를 설정해야 한다 — 이 파일 전체에 E402(모듈
상단 이후 import) 예외를 적용한다."""
# ruff: noqa: E402
import os
import sys
from pathlib import Path

os.environ.setdefault(
    # ⚠️ 2026-09-08 심각한 버그 수정: 이전엔 실제 개발용 DB("aimock")를
    # 그대로 가리키고 있었음 — 매 테스트 전 전체 TRUNCATE를 실행하는
    # `_clean_db` 픽스처 때문에, pytest를 돌릴 때마다 실사용 중이던 회원
    # 가입 계정/면접 데이터가 전부 삭제되고 있었다(사용자가 실제로 로그인
    # 안 되는 문제로 발견). 반드시 별도 DB("aimock_test")를 써야 한다.
    "DATABASE_URL", "postgresql+asyncpg://aimock:aimock_dev_only@localhost:55432/aimock_test"
)
# ⚠️ 2026-09-09 재발 — 같은 부류의 사고가 다른 경로로 다시 일어남:
# `docker compose exec app pytest ...`로 컨테이너 안에서 이 테스트를
# 돌리면, 컨테이너의 실행 환경에 이미 `DATABASE_URL`이 **실제 개발 DB
# ("aimock")로 설정되어 있어서**(docker-compose.yml의 `app` 서비스
# environment) 위 `setdefault`가 아무 효과가 없었다 — "이미 설정돼 있으면
# 그대로 둔다"는 setdefault의 정의상 당연한 동작인데, 이번엔 그 "이미
# 설정된 값"이 하필 진짜 개발 DB였다. 그 결과 `_clean_db`가 로컬 dev DB
# 전체를 TRUNCATE해버림(실제로 발생 — 내부테스트결과서 참조). 재발 방지로
# **최종적으로 확정된 DATABASE_URL이 테스트 전용 DB가 아니면 이 시점에서
# 바로 죽인다** — 아무리 실행 방식이 달라져도(로컬 host, Docker exec,
# CI 등) 이 방어선 하나만은 항상 통과해야 실제 파괴적 TRUNCATE로 진행됨.
_resolved_db_url = os.environ["DATABASE_URL"]
if "_test" not in _resolved_db_url.rsplit("/", 1)[-1]:
    raise RuntimeError(
        "테스트가 테스트 전용 DB가 아닌 곳을 가리키고 있습니다: "
        f"{_resolved_db_url!r} — 이 DB 이름에 '_test'가 없습니다. "
        "이 테스트 스위트는 모든 테이블을 TRUNCATE하므로, 실수로 개발/운영 "
        "DB를 대상으로 실행되는 것을 막기 위해 여기서 중단합니다. "
        "DATABASE_URL 환경변수가 어디서 설정됐는지(.env, docker-compose "
        "environment, 셸 export 등) 확인하고 *_test로 끝나는 DB로 "
        "바꾸세요."
    )

os.environ.setdefault("JWT_SECRET", "test-only-secret")
# 2026-09-09(F-4, AES-256-GCM 전환): 이전 값은 Fernet(AES-128)용으로 만든
# 키였음 — 우연히 32바이트라 새 방식에서도 길이 검증은 통과했겠지만,
# 서로 다른 목적으로 만든 키를 재사용하지 않는다는 원칙(app/core/crypto.py
# 에러 메시지에도 명시)을 테스트 코드도 그대로 지키기 위해 새로 발급.
os.environ.setdefault("MEDIA_ENCRYPTION_KEY", "g8Y6tAvfu1D0t88_Yj3XWEeAraqZdnZZM6lv_Mm1WxA=")
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
    get_whiteboard_evaluator,
)
from app.db import AsyncSessionLocal, Base, engine
from app.main import app

from fakes import (
    FakeEmotionAnalyzer,
    FakeLLMProvider,
    FakeProsodyAnalyzer,
    FakeReportGenerator,
    FakeSTTProvider,
    FakeWhiteboardEvaluator,
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


@pytest.fixture(autouse=True)
def _fake_whiteboard_evaluator():
    """aimock_u2c_trd.md — 실제 Gemini Vision 대신 Fake로 검증."""
    fake_whiteboard = FakeWhiteboardEvaluator()
    app.dependency_overrides[get_whiteboard_evaluator] = lambda: fake_whiteboard
    yield fake_whiteboard
    app.dependency_overrides.pop(get_whiteboard_evaluator, None)


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
