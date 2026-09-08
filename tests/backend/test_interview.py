"""docs/trd/aimock_u2a_trd.md §5/§6 + aimock_u3a_trd.md AC-1/3/4 대응 테스트."""

from sqlalchemy import select

from app.models.interview import Interview
from app.models.media_asset import MediaAsset


async def _signup_and_login(client, email="candidate@example.com"):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123", "role": "candidate"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return login.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_ac1_start_interview_creates_live_session_with_opening_question(client, db_session):
    token = await _signup_and_login(client)
    resp = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["question_text"]

    interview = await db_session.get(Interview, body["interview_id"])
    assert interview.status == "live"


async def test_ac2_turn_saves_user_and_ai_transcripts(client, db_session, _fake_providers):
    token = await _signup_and_login(client)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        headers=_auth(token),
        data={"turn_index": "0"},
        files={"audio": ("a.webm", "MSA 경험이 있습니다.".encode("utf-8"), "audio/webm")},
    )
    assert resp.status_code == 200
    assert resp.json()["question_text"]

    from app.models.transcript import Transcript

    rows = list(
        (
            await db_session.scalars(
                select(Transcript).where(Transcript.interview_id == interview_id)
            )
        ).all()
    )
    speakers = sorted(r.speaker for r in rows)
    assert speakers == ["ai", "ai", "user"]  # 오프닝 질문 + 사용자 답변 + 다음 질문


async def test_ac2b_turn_persists_original_audio_as_encrypted_media(client, db_session, _fake_providers):
    """2026-09-08 추가 — 마스터 TRD §3 N-003/ADR-004 재검토에서 발견한 갭:
    턴 제출이 STT에만 오디오를 쓰고 U1-b 암호화 저장을 호출하지 않던 것을
    고침. 원본 미디어가 실제로 media_assets에 남아야 AC-M6(리포트 화면에서
    삭제)가 의미를 가진다."""
    token = await _signup_and_login(client)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        headers=_auth(token),
        data={"turn_index": "0"},
        files={"audio": ("a.webm", b"fake-audio-bytes", "audio/webm")},
    )
    assert resp.status_code == 200

    assets = list(
        (
            await db_session.scalars(
                select(MediaAsset).where(MediaAsset.interview_id == interview_id)
            )
        ).all()
    )
    assert len(assets) == 1
    assert assets[0].kind == "audio"
    assert assets[0].turn_index == 0
    assert assets[0].encrypted is True


async def test_ac2c_candidate_can_list_and_delete_own_turn_media(client, _fake_providers):
    """AC-M6 — 리포트 화면에서 원본 오디오 삭제 요청이 실제로 가능해야 함."""
    token = await _signup_and_login(client)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]
    await client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        headers=_auth(token),
        data={"turn_index": "0"},
        files={"audio": ("a.webm", b"fake-audio-bytes", "audio/webm")},
    )

    listed = await client.get(
        f"/api/v1/interviews/{interview_id}/media", headers=_auth(token)
    )
    assert listed.status_code == 200
    media = listed.json()
    assert len(media) == 1
    assert media[0]["kind"] == "audio"

    deleted = await client.delete(f"/api/v1/media/{media[0]['id']}", headers=_auth(token))
    assert deleted.status_code == 204

    listed_again = await client.get(
        f"/api/v1/interviews/{interview_id}/media", headers=_auth(token)
    )
    assert listed_again.json() == []


async def test_ac3_long_answer_skips_llm_call(client, _fake_providers):
    fake_llm, _fake_stt = _fake_providers
    token = await _signup_and_login(client)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    long_text = "가" * 801
    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        headers=_auth(token),
        data={"turn_index": "0"},
        files={"audio": ("a.webm", long_text.encode("utf-8"), "audio/webm")},
    )
    assert resp.status_code == 200
    assert "다음 질문으로 넘어가겠습니다" in resp.json()["question_text"]
    assert fake_llm.call_count == 0


async def test_ac4_llm_end_signal_completes_interview(client, db_session, _fake_providers):
    fake_llm, _fake_stt = _fake_providers
    fake_llm.action = "end_interview"
    fake_llm.reply_text = "면접을 종료하겠습니다. 수고하셨습니다."

    token = await _signup_and_login(client)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        headers=_auth(token),
        data={"turn_index": "0"},
        files={"audio": ("a.webm", "짧은 답변입니다.".encode("utf-8"), "audio/webm")},
    )
    assert resp.status_code == 200
    assert resp.json()["ended"] is True

    interview = await db_session.get(Interview, interview_id)
    assert interview.status == "completed"
    assert interview.ended_at is not None


async def test_ac5_manual_end(client, db_session):
    token = await _signup_and_login(client)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(f"/api/v1/interviews/{interview_id}/end", headers=_auth(token))
    assert resp.status_code == 204

    interview = await db_session.get(Interview, interview_id)
    assert interview.status == "completed"


async def test_ac6_other_users_interview_forbidden(client):
    owner_token = await _signup_and_login(client, email="owner2@example.com")
    other_token = await _signup_and_login(client, email="other2@example.com")

    start = await client.post(
        "/api/v1/interviews", headers=_auth(owner_token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        headers=_auth(other_token),
        data={"turn_index": "0"},
        files={"audio": ("a.webm", b"hi", "audio/webm")},
    )
    assert resp.status_code == 403


async def test_ac7_turn_on_completed_interview_returns_409(client):
    token = await _signup_and_login(client)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]
    await client.post(f"/api/v1/interviews/{interview_id}/end", headers=_auth(token))

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        headers=_auth(token),
        data={"turn_index": "0"},
        files={"audio": ("a.webm", b"hi", "audio/webm")},
    )
    assert resp.status_code == 409


async def test_u3a_ac3_retrieve_candidates_filters_by_category(db_session):
    from app.services import question_service

    await question_service.seed_if_empty(db_session)
    results = await question_service.retrieve_candidates(db_session, category="backend", limit=10)
    assert results
    assert all(r.category == "backend" for r in results)


async def test_ac9_retrieve_candidates_excludes_already_asked_questions(db_session):
    """2026-09-08 회귀 테스트 — 실사용 중 발견한 "AI가 같은 질문을 계속
    반복한다" 버그. 원인은 이 함수가 이미 나온 질문도 다시 무작위로 뽑을
    수 있었던 것(LLM 제공자와 무관, 실제 Groq로 재현 확인). 이미 나온
    질문은 후보에서 빠져야 한다."""
    from app.services import question_service

    await question_service.seed_if_empty(db_session)
    all_questions = await question_service.retrieve_candidates(db_session, limit=100)
    assert len(all_questions) >= 2  # 시드 질문이 최소 2개는 있어야 의미있는 테스트

    already_asked = [q.content for q in all_questions[:-1]]  # 마지막 1개만 안 나온 걸로
    remaining = await question_service.retrieve_candidates(
        db_session, limit=100, exclude_contents=already_asked
    )
    remaining_contents = {q.content for q in remaining}
    assert remaining_contents.isdisjoint(already_asked)
    assert all_questions[-1].content in remaining_contents


async def test_u3a_ac4_llm_schema_violation_falls_back():
    from app.ai.llm import FALLBACK_REPLY, _parse_or_fallback

    result = _parse_or_fallback("this is not valid json at all")
    assert result.reply_text == FALLBACK_REPLY
    assert result.action == "ask_question"

    result2 = _parse_or_fallback('{"reply_text": "hi", "action": "not_a_valid_action"}')
    assert result2.reply_text == FALLBACK_REPLY


async def test_ac8_missing_gemini_key_raises_service_unavailable_not_500():
    """GEMINI_API_KEY 미설정 시 500이 아니라 503(ServiceUnavailableError) — 실제
    Docker 컨테이너 테스트로 500이 나는 걸 발견하고 고친 버그(A0 §3)."""
    import pytest

    from app.ai.llm import GeminiProvider
    from app.config import settings
    from app.core.errors import ServiceUnavailableError

    original_key = settings.gemini_api_key
    settings.gemini_api_key = None
    try:
        provider = GeminiProvider()
        with pytest.raises(ServiceUnavailableError):
            provider._get_client()
    finally:
        settings.gemini_api_key = original_key
