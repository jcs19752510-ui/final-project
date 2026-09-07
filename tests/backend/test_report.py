"""docs/trd/aimock_u4_trd.md §5/§6."""

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


async def test_ac9_no_media_gives_empty_emotion_and_prosody(client, db_session):
    """U3-b AC-4 — video_frame/audio 미디어가 없으면 조용히 빈 배열(회귀 아님)."""
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    assert resp.status_code == 201
    details = resp.json()["details_json"]
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

    resp = await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    assert resp.status_code == 201
    details = resp.json()["details_json"]

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

    resp = await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    assert resp.status_code == 201
    body = resp.json()
    assert body["technical_score"] == 4
    assert body["summary_text"]

    saved = await db_session.scalar(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview.id)
    )
    assert saved is not None


async def test_ac3_regeneration_overwrites_not_duplicates(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))

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

    await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
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

    resp = await client.post(f"/api/v1/interviews/{interview.id}/report", headers=_auth(token))
    keywords = resp.json()["details_json"]["keywords"]
    assert "MSA" in keywords
