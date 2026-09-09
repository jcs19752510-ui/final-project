"""docs/trd/aimock_u2c_trd.md §5/§6 (2026-09-09 신규, 원안 F-005 착수).
FakeWhiteboardEvaluator로 Gemini Vision 호출 없이 서비스/API 계약을 검증한다."""

from sqlalchemy import select

from app.models.interview import Interview
from app.models.user import User
from app.models.whiteboard_snapshot import WhiteboardSnapshot

_PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000a49444154789c6360000002000100ffff03000006"
    "0005570d6a0000000049454e44ae426082"
)


async def _signup_and_login(client, email="wb-candidate@example.com"):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123", "role": "candidate"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return login.json()["access_token"]


async def _make_interview(db_session, candidate_email="wb-candidate@example.com") -> Interview:
    user = await db_session.scalar(select(User).where(User.email == candidate_email))
    interview = Interview(candidate_id=user.id, job_role="backend")
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    return interview


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_ac1_upload_returns_ai_feedback(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/whiteboard-snapshots",
        headers=_auth(token),
        files={"file": ("board.png", _PNG_1x1, "image/png")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["ai_feedback_text"]
    assert "id" in body


async def test_ac2_snapshot_saved_encrypted_and_not_plaintext(client, db_session, tmp_path, monkeypatch):
    import app.config as config_module

    monkeypatch.setattr(config_module.settings, "media_storage_dir", str(tmp_path))

    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/whiteboard-snapshots",
        headers=_auth(token),
        files={"file": ("board.png", _PNG_1x1, "image/png")},
    )
    snapshot_id = resp.json()["id"]

    saved = await db_session.get(WhiteboardSnapshot, snapshot_id)
    assert saved is not None
    from pathlib import Path

    stored_bytes = Path(saved.image_ref).read_bytes()
    assert stored_bytes != _PNG_1x1  # 평문 PNG 그대로 저장되지 않음(암호화됨)


async def test_ac3_list_returns_snapshots_in_order(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    await client.post(
        f"/api/v1/interviews/{interview.id}/whiteboard-snapshots",
        headers=_auth(token),
        files={"file": ("board1.png", _PNG_1x1, "image/png")},
    )
    await client.post(
        f"/api/v1/interviews/{interview.id}/whiteboard-snapshots",
        headers=_auth(token),
        files={"file": ("board2.png", _PNG_1x1, "image/png")},
    )

    resp = await client.get(
        f"/api/v1/interviews/{interview.id}/whiteboard-snapshots", headers=_auth(token)
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_ac4_other_users_interview_forbidden(client, db_session):
    await _signup_and_login(client, email="wb-owner@example.com")
    other_token = await _signup_and_login(client, email="wb-other@example.com")
    interview = await _make_interview(db_session, candidate_email="wb-owner@example.com")

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/whiteboard-snapshots",
        headers=_auth(other_token),
        files={"file": ("board.png", _PNG_1x1, "image/png")},
    )
    assert resp.status_code == 403


async def test_ac5_non_image_content_type_rejected(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/whiteboard-snapshots",
        headers=_auth(token),
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 415


async def test_ac6_oversized_file_rejected(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    big = b"\x00" * (10 * 1024 * 1024 + 1)
    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/whiteboard-snapshots",
        headers=_auth(token),
        files={"file": ("board.png", big, "image/png")},
    )
    assert resp.status_code == 413
