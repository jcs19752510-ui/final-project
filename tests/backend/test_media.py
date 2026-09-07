"""docs/trd/aimock_u1b_trd.md §5/§6 대응 테스트."""

from sqlalchemy import select

from app.core.crypto import decrypt_bytes
from app.models.interview import Interview
from app.models.media_asset import MediaAsset
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


async def _make_interview(db_session, candidate_email="candidate@example.com") -> Interview:
    user = await db_session.scalar(select(User).where(User.email == candidate_email))
    interview = Interview(candidate_id=user.id, job_role="backend")
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    return interview


async def test_ac1_upload_encrypts_file(client, db_session, tmp_path):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    raw = b"raw-audio-bytes-not-encrypted"
    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/media",
        headers=headers,
        data={"kind": "audio", "turn_index": "1"},
        files={"file": ("turn1.webm", raw, "audio/webm")},
    )
    assert resp.status_code == 201
    media_id = resp.json()["id"]

    asset = await db_session.get(MediaAsset, media_id)
    stored = open(asset.storage_path, "rb").read()
    assert stored != raw  # 평문으로 저장되지 않음
    assert decrypt_bytes(stored) == raw  # 복호화하면 원본과 일치


async def test_ac2_delete_removes_file_and_record(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        f"/api/v1/interviews/{interview.id}/media",
        headers=headers,
        data={"kind": "audio", "turn_index": "1"},
        files={"file": ("turn1.webm", b"data", "audio/webm")},
    )
    media_id = upload.json()["id"]
    asset = await db_session.get(MediaAsset, media_id)
    path = asset.storage_path

    delete = await client.delete(f"/api/v1/media/{media_id}", headers=headers)
    assert delete.status_code == 204

    import os

    assert not os.path.exists(path)
    assert await db_session.get(MediaAsset, media_id) is None


async def test_ac3_delete_already_deleted_returns_404(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        f"/api/v1/interviews/{interview.id}/media",
        headers=headers,
        data={"kind": "audio", "turn_index": "1"},
        files={"file": ("turn1.webm", b"data", "audio/webm")},
    )
    media_id = upload.json()["id"]

    first = await client.delete(f"/api/v1/media/{media_id}", headers=headers)
    assert first.status_code == 204
    second = await client.delete(f"/api/v1/media/{media_id}", headers=headers)
    assert second.status_code == 404


async def test_ac4_other_users_media_forbidden(client, db_session):
    owner_token = await _signup_and_login(client, email="owner@example.com")
    other_token = await _signup_and_login(client, email="other@example.com")
    interview = await _make_interview(db_session, candidate_email="owner@example.com")

    upload = await client.post(
        f"/api/v1/interviews/{interview.id}/media",
        headers={"Authorization": f"Bearer {owner_token}"},
        data={"kind": "audio", "turn_index": "1"},
        files={"file": ("turn1.webm", b"data", "audio/webm")},
    )
    media_id = upload.json()["id"]

    resp = await client.delete(
        f"/api/v1/media/{media_id}", headers={"Authorization": f"Bearer {other_token}"}
    )
    assert resp.status_code == 403


async def test_ac5_purge_user_media_removes_all_assets(client, db_session):
    from app.services.media_service import purge_user_media

    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        f"/api/v1/interviews/{interview.id}/media",
        headers=headers,
        data={"kind": "audio", "turn_index": "1"},
        files={"file": ("turn1.webm", b"data", "audio/webm")},
    )
    media_id = upload.json()["id"]
    asset = await db_session.get(MediaAsset, media_id)
    path = asset.storage_path

    user = await db_session.scalar(select(User).where(User.email == "candidate@example.com"))
    await purge_user_media(db_session, user.id)
    await db_session.commit()

    import os

    assert not os.path.exists(path)
    assert await db_session.get(MediaAsset, media_id) is None
