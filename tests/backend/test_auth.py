"""docs/trd/aimock_u1_trd.md §5/§6 대응 테스트."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.user import User


async def _signup(client, email="candidate@example.com", password="password123", role="candidate"):
    return await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "role": role},
    )


async def test_ac1_signup_hashes_password(client, db_session):
    resp = await _signup(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "candidate@example.com"
    assert body["role"] == "candidate"

    user = await db_session.scalar(select(User).where(User.email == "candidate@example.com"))
    assert user is not None
    assert user.password_hash != "password123"
    assert user.password_hash.startswith("$2b$")  # bcrypt


async def test_ac2_duplicate_signup_returns_409(client):
    await _signup(client)
    resp = await _signup(client)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "DUPLICATE_EMAIL"


async def test_ac3_login_success_and_wrong_password(client):
    await _signup(client)

    ok = await client.post(
        "/api/v1/auth/login",
        json={"email": "candidate@example.com", "password": "password123"},
    )
    assert ok.status_code == 200
    assert "access_token" in ok.json()

    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "candidate@example.com", "password": "wrong-password"},
    )
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_ac4_me_without_token_returns_401(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "NOT_AUTHENTICATED"


async def test_ac5_withdraw_then_token_becomes_invalid(client):
    await _signup(client)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "candidate@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    withdraw = await client.post("/api/v1/auth/withdraw", headers=headers)
    assert withdraw.status_code == 204

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 401


async def test_ac6_relogin_within_grace_period_restores_account(client, db_session):
    await _signup(client)
    login1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "candidate@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login1.json()['access_token']}"}
    await client.post("/api/v1/auth/withdraw", headers=headers)

    login2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "candidate@example.com", "password": "password123"},
    )
    assert login2.status_code == 200

    user = await db_session.scalar(select(User).where(User.email == "candidate@example.com"))
    assert user.deleted_at is None
    assert user.purge_at is None


async def test_ac7_purge_expired_users_deletes_record(client, db_session):
    from app.services.user_service import purge_expired_users

    await _signup(client)
    user = await db_session.scalar(select(User).where(User.email == "candidate@example.com"))
    now = datetime.now(timezone.utc)
    user.deleted_at = now - timedelta(days=31)
    user.purge_at = now - timedelta(days=1)  # 이미 유예기간 경과
    await db_session.commit()

    purged_ids = await purge_expired_users(db_session)
    assert user.id in purged_ids

    remaining = await db_session.scalar(select(User).where(User.email == "candidate@example.com"))
    assert remaining is None
