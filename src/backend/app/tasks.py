"""Celery 태스크 — 현재는 리포트 생성 1개뿐(ADR-003 갱신, app/celery_app.py 참조).

태스크 인자는 반드시 직렬화 가능한 값(str)만 받는다 — 실행 provider
(LLM/감정/음성 분석기)는 Redis를 거쳐 워커로 전달할 수 없는 라이브
객체(API 클라이언트 등)라서, 태스크 함수 안에서 워커 프로세스 자신의
싱글턴(`app.ai.providers`)을 직접 호출해 얻는다.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from app.celery_app import celery_app
from app.db import engine

logger = logging.getLogger("aimock.tasks")


async def _run_and_dispose(interview_id: UUID) -> None:
    """asyncpg 커넥션 풀은 그걸 만든 이벤트 루프에 묶인다. 이 태스크가
    호출될 때마다(특히 `asyncio.run()`으로) 매번 새 이벤트 루프가 생기므로,
    프로세스 전역 `engine`(app/db.py, 모듈 임포트 시 1회만 생성됨)의 풀을
    작업이 끝날 때마다 명시적으로 `dispose()`하지 않으면, 같은 워커
    프로세스가 처리하는 두 번째 태스크부터 "이미 닫힌 루프에 묶인 커넥션"
    오류가 난다(asyncpg+asyncio.run() 반복 호출의 잘 알려진 함정 — AWS
    Lambda+asyncpg 사례와 동일 원인). 매번 dispose 후 다음 태스크에서
    지연 재연결되므로 기능 손실은 없다."""
    # 순환 임포트 회피(app.ai.providers → app.tasks 방향 의존은 없지만,
    # 워커 기동 시점의 임포트 순서 부담을 줄이기 위해 함수 내부에서 임포트).
    from app.ai.providers import get_emotion_analyzer, get_prosody_analyzer, get_report_generator
    from app.services import report_service

    try:
        await report_service.run_report_generation(
            interview_id,
            get_report_generator(),
            get_emotion_analyzer(),
            get_prosody_analyzer(),
        )
    finally:
        await engine.dispose()


def _run_async(interview_id: UUID) -> None:
    """이미 실행 중인 이벤트 루프 안에서 호출되는 경우(테스트에서
    `CELERY_TASK_ALWAYS_EAGER=True`일 때 `.delay()`가 FastAPI 라우트의
    async 컨텍스트 안에서 곧바로 동기 실행됨 — pytest-asyncio가 이미
    이벤트 루프를 돌리고 있는 상태)와, 실제 Celery 워커 프로세스처럼 실행
    중인 루프가 전혀 없는 경우를 둘 다 지원해야 한다. 전자에서
    `asyncio.run()`을 그대로 부르면 `RuntimeError: asyncio.run() cannot be
    called from a running event loop`가 난다 — 실제로 재현해서 확인 후
    분기 처리함."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_run_and_dispose(interview_id))
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(asyncio.run, _run_and_dispose(interview_id)).result()


@celery_app.task(name="aimock.run_report_generation")
def run_report_generation_task(interview_id: str) -> None:
    try:
        _run_async(UUID(interview_id))
    except Exception:
        # report_service.run_report_generation 내부에서 이미 실패를
        # report.status="failed"로 흡수한다(report_service.py 참조). 여기서
        # 또 예외를 던지면 Celery가 재시도/에러로그를 남기는 게 아니라
        # 태스크 자체가 "실패"로 기록될 뿐 사용자에게 닿는 경로는 없으므로,
        # 로그만 남기고 삼킨다(이미 실패 상태가 DB에 저장돼 있어 폴링하는
        # 사용자는 정상적으로 실패를 인지할 수 있음).
        logger.exception("리포트 생성 태스크 실행 중 처리 안 된 예외(interview_id=%s)", interview_id)
