"""ADR-003 갱신(2026-09-18): Celery+Redis 재도입.

원본 계획서(§4.2.3)는 "실시간성이 덜 중요한 작업(리포트 생성 등)"을
Celery+Redis로 비동기 처리하도록 설계했다. ADR-003(2026-09-07)은 1인
개발자가 컨테이너 3개(Postgres/Redis/Celery worker)를 운영하는 부담을
이유로 FastAPI `BackgroundTasks`로 대체했었고, 2026-09-08에 실제로
BackgroundTasks 기반 비동기화까지 검증 완료한 상태였다. 그럼에도
2026-09-18 사용자가 "원본과 맞추고 싶다"고 명시적으로 재도입을 요청해
이 모듈을 추가한다 — BackgroundTasks가 문제가 있어서가 아니라, 원본
아키텍처에 정합시키는 것 자체가 목적인 결정이다(harness_06 §3
"이름만 맞추는 정합"과는 달리, 이번엔 실제로 별도 워커 프로세스가
큐를 소비하는 구조까지 실질적으로 구현한다).
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "aimock",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,  # eager(테스트) 모드에서 태스크 예외가 조용히 묻히지 않게 함
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# 워커가 기동할 때 태스크 모듈이 실제로 임포트되어 등록되도록 명시적으로
# import한다(celery_app.conf.imports보다 단순 — 워커/웹 두 프로세스가
# 같은 코드베이스를 쓰므로 순환 임포트 걱정 없음).
import app.tasks  # noqa: E402,F401
