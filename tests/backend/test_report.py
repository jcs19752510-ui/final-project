"""docs/trd/aimock_u4_trd.md §5/§6.

2026-09-08(§3-1): 리포트 생성이 동기 처리에서 백그라운드 처리로 바뀌면서
POST 응답 자체는 항상 `status="processing"`(점수 없음)만 담고, 실제 결과는
뒤이은 GET으로 확인해야 한다. httpx `ASGITransport`는 FastAPI
`BackgroundTasks`를 응답 조립 이후·`client.post()`가 반환되기 이전에
전부 실행하므로(실측 확인, 내부테스트결과서 참조), 테스트에서는 POST 직후
바로 GET해도 sleep 없이 완료된 결과를 볼 수 있다 — 다만 POST 자체의
응답 바디는 항상 processing 상태라는 점이 실제 프로덕션(uvicorn)과 동일한
계약이다.
"""

from sqlalchemy import select

from app.models.evaluation_report import EvaluationReport
from app.models.interview import Interview
from app.models.transcript import Transcript
from app.models.user import User


async def _signup_and_login(client, email="candidate@example.com"):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123", "role": "candidate"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return login.json()["access_token"]


async def _make_interview(
    db_session, candidate_email="candidate@example.com", status="completed"
) -> Interview:
    user = await db_session.scalar(select(User).where(User.email == candidate_email))
    interview = Interview(candidate_id=user.id, job_role="backend", status=status)
    db_session.add(interview)
    await db_session.flush()
    db_session.add(
        Transcript(interview_id=interview.id, turn_index=0, speaker="ai", text="자기소개해주세요.")
    )
    db_session.add(
        Transcript(
            interview_id=interview.id,
            turn_index=0,
            speaker="user",
            text="MSA MSA MSA 트랜잭션 관리 경험이 있습니다.",
        )
    )
    await db_session.commit()
    await db_session.refresh(interview)
    return interview


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _generate_and_fetch(client, token: str, interview_id) -> dict:
    """POST(202, processing)로 생성을 시작시키고, 곧바로 GET으로 최종
    상태를 읽어온다(위 모듈 docstring 참조 — 테스트 환경에선 sleep 불필요)."""
    post_resp = await client.post(f"/api/v1/interviews/{interview_id}/report", headers=_auth(token))
    assert post_resp.status_code == 202
    assert post_resp.json()["status"] == "processing"

    get_resp = await client.get(f"/api/v1/interviews/{interview_id}/report", headers=_auth(token))
    assert get_resp.status_code == 200
    return get_resp.json()


async def test_ac9_no_media_gives_empty_emotion_and_prosody(client, db_session):
    """U3-b AC-4 — video_frame/audio 미디어가 없으면 조용히 빈 배열(회귀 아님)."""
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    body = await _generate_and_fetch(client, token, interview.id)
    assert body["status"] == "completed"
    details = body["details_json"]
    assert details["emotion_timeline"] == []
    assert details["voice_prosody"] == []


async def test_ac10_video_frame_and_audio_media_populate_emotion_and_prosody(
    client, db_session, _fake_emotion_prosody_analyzers
):
    """U3-b AC-5 — video_frame/audio 미디어가 있으면 분석 결과가 채워진다."""
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    await client.post(
        f"/api/v1/interviews/{interview.id}/media",
        headers=_auth(token),
        data={"kind": "video_frame", "turn_index": "0"},
        files={"file": ("frame.jpg", b"fake-jpeg-bytes", "image/jpeg")},
    )
    await client.post(
        f"/api/v1/interviews/{interview.id}/media",
        headers=_auth(token),
        data={"kind": "audio", "turn_index": "0"},
        files={"file": ("turn.webm", b"fake-audio-bytes", "audio/webm")},
    )

    body = await _generate_and_fetch(client, token, interview.id)
    details = body["details_json"]

    assert details["emotion_timeline"] == [
        {"turn_index": 0, "dominant_emotion": "neutral", "confidence": 0.9}
    ]
    assert details["voice_prosody"] == [
        {"turn_index": 0, "pitch_mean_hz": 180.0, "energy_mean": 0.03}
    ]

    fake_emotion, fake_prosody = _fake_emotion_prosody_analyzers
    assert fake_emotion.call_count == 1
    assert fake_prosody.call_count == 1


async def test_ac1_report_on_live_interview_returns_409(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session, status="live")

    resp = await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    assert resp.status_code == 409


async def test_ac2_report_generated_on_completed_interview(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    body = await _generate_and_fetch(client, token, interview.id)
    assert body["status"] == "completed"
    assert body["technical_score"] == 4
    assert body["summary_text"]

    saved = await db_session.scalar(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview.id)
    )
    assert saved is not None
    assert saved.status == "completed"


async def test_ac3_regeneration_overwrites_not_duplicates(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    await _generate_and_fetch(client, token, interview.id)
    await _generate_and_fetch(client, token, interview.id)

    from sqlalchemy import func

    count = await db_session.scalar(
        select(func.count())
        .select_from(EvaluationReport)
        .where(EvaluationReport.interview_id == interview.id)
    )
    assert count == 1


async def test_ac4_get_report_before_generation_returns_404(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.get(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    assert resp.status_code == 404


async def test_ac5_get_report_returns_generated_content(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    await _generate_and_fetch(client, token, interview.id)
    resp = await client.get(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["technical_score"] == 4


async def test_ac6_other_users_report_forbidden(client, db_session):
    await _signup_and_login(client, email="owner4@example.com")
    other_token = await _signup_and_login(client, email="other4@example.com")
    interview = await _make_interview(db_session, candidate_email="owner4@example.com")

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/report", headers=_auth(other_token)
    )
    assert resp.status_code == 403

    resp2 = await client.get(f"/api/v1/interviews/{interview.id}/report", headers=_auth(other_token))
    assert resp2.status_code == 403


async def test_ac7_missing_gemini_key_raises_service_unavailable():
    import pytest

    from app.ai.report import GeminiReportGenerator
    from app.config import settings
    from app.core.errors import ServiceUnavailableError

    original_key = settings.gemini_api_key
    settings.gemini_api_key = None
    try:
        generator = GeminiReportGenerator()
        with pytest.raises(ServiceUnavailableError):
            generator._get_client()
    finally:
        settings.gemini_api_key = original_key


async def test_ac8_keyword_extraction_finds_repeated_word(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    body = await _generate_and_fetch(client, token, interview.id)
    assert "MSA" in body["details_json"]["keywords"]


async def test_u4_ac9_post_response_is_immediately_processing_not_final_data(client, db_session):
    """2026-09-08(§3-1) 신규 — 운영 환경에서 리포트 생성이 1분 이상 걸리던
    문제 수정의 핵심 계약: POST 응답 자체는 무거운 분석을 기다리지 않고
    즉시 202 + processing 상태만 반환해야 한다(점수/세부사항 없음)."""
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "processing"
    assert body["technical_score"] is None
    assert body["error_message"] is None


async def test_u4_ac10_generation_failure_sets_failed_status_with_safe_message(
    client, db_session, _fake_report_generator
):
    """2026-09-08(§3-1) 신규 — 백그라운드 작업 중 예외가 나도 서버가 죽지
    않고(요청은 이미 끝났으므로 애초에 죽을 수 없음), 리포트 상태를
    "failed"로 남겨 사용자가 GET으로 확인·재시도할 수 있어야 한다.
    노출되는 메시지는 원본 예외 문자열이 아니라 안전한 일반 문구여야
    한다(내부 정보 유출 방지 — 보안 관점)."""
    from app.services.report_service import GENERIC_FAILURE_MESSAGE

    _fake_report_generator.raise_exc = RuntimeError("secret internal db connection string leaked")

    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    resp = await client.get(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert body["error_message"] == GENERIC_FAILURE_MESSAGE
    assert "secret internal db connection string" not in (body["error_message"] or "")


async def test_u4_ac11_start_generation_is_idempotent_while_still_processing(db_session):
    """2026-09-08(§3-1) 신규 — `_enforce`류 안전장치와 같은 취지: 이미
    처리 중인 리포트에 다시 시작 요청이 오면(예: 중복 클릭) 새 백그라운드
    작업을 또 예약하지 않아야 한다(동시 실행으로 인한 DB 경합/중복 CPU
    낭비 방지). `start_report_generation`을 직접 호출해 `should_run`
    플래그로 검증 — HTTP 계층에서는 `ASGITransport`가 백그라운드 작업을
    항상 완료 상태까지 실행해버려 "아직 처리 중"인 순간을 포착할 수
    없으므로(모듈 docstring 참조) 서비스 함수를 직접 테스트한다."""
    from app.services import report_service

    user = User(email="idem@example.com", password_hash="x", role="candidate")
    db_session.add(user)
    await db_session.flush()
    interview = Interview(candidate_id=user.id, job_role="backend", status="completed")
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    report1, should_run1 = await report_service.start_report_generation(
        db_session, interview.id, user.id
    )
    assert should_run1 is True
    assert report1.status == "processing"

    report2, should_run2 = await report_service.start_report_generation(
        db_session, interview.id, user.id
    )
    assert should_run2 is False  # 이미 processing이고 아직 stale 아님 — 재실행 안 함
    assert report2.id == report1.id


async def test_u4_ac12_stale_processing_report_allows_retry(db_session):
    """2026-09-08(§3-1) 신규 — 서버 재시작 등으로 백그라운드 작업이 중간에
    죽으면 리포트가 "processing"에 영원히 멈출 수 있다. 마지막 시작 시각이
    `PROCESSING_STALE_AFTER`보다 오래됐으면 재시도를 허용해야 한다."""
    from datetime import datetime, timedelta, timezone

    from app.services import report_service

    user = User(email="stale@example.com", password_hash="x", role="candidate")
    db_session.add(user)
    await db_session.flush()
    interview = Interview(candidate_id=user.id, job_role="backend", status="completed")
    db_session.add(interview)
    await db_session.flush()
    stale_report = EvaluationReport(
        interview_id=interview.id,
        status="processing",
        processing_started_at=datetime.now(timezone.utc)
        - report_service.PROCESSING_STALE_AFTER
        - timedelta(minutes=1),
        details_json={},
    )
    db_session.add(stale_report)
    await db_session.commit()

    report, should_run = await report_service.start_report_generation(
        db_session, interview.id, user.id
    )
    assert should_run is True  # 오래 멈춰있던 processing이므로 재시도 허용
    assert report.status == "processing"
    assert report.processing_started_at > (
        datetime.now(timezone.utc) - timedelta(seconds=10)
    )
