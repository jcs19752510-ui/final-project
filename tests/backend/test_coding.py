"""docs/trd/aimock_u2b_trd.md §5/§6. 실제 subprocess로 실행(mock 없음)."""

import shutil

import pytest
from sqlalchemy import select

from app.models.coding_submission import CodingSubmission
from app.models.interview import Interview
from app.models.user import User

# JavaScript 테스트(2026-09-09)는 리눅스 컨테이너에 `node`가 설치돼 있어야
# 하므로, node 없는 로컬 환경(Windows 등)에서는 스킵한다 — Python 샌드박스
# 테스트(test_sandbox_hardening.py)가 seccomp에 쓰는 것과 동일한 skipif 패턴.
pytestmark_js = pytest.mark.skipif(shutil.which("node") is None, reason="node 미설치 환경(로컬 Windows 등)")


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


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_ac1_normal_code_executes_successfully(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "python", "code": "print('hi')"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "hi" in body["stdout"]
    assert body["exit_code"] == 0
    assert body["timed_out"] is False


async def test_ac2_infinite_loop_times_out(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "python", "code": "while True:\n    pass"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["timed_out"] is True
    assert body["exit_code"] is None


async def test_ac3_app_secrets_not_leaked_to_child_process(client, db_session, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://should-not-leak")
    monkeypatch.setenv("JWT_SECRET", "super-secret-value-should-not-leak")
    monkeypatch.setenv("MEDIA_ENCRYPTION_KEY", "media-secret-should-not-leak")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret-should-not-leak")

    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "python", "code": "import os\nprint(dict(os.environ))"},
    )
    assert resp.status_code == 201
    stdout = resp.json()["stdout"]
    assert "should-not-leak" not in stdout
    assert "DATABASE_URL" not in stdout
    assert "JWT_SECRET" not in stdout


async def test_ac4_submission_saved_to_db(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "python", "code": "print(1+1)"},
    )
    submission_id = resp.json()["submission_id"]

    saved = await db_session.get(CodingSubmission, submission_id)
    assert saved is not None
    assert saved.exec_result_json["stdout"].strip() == "2"


async def test_ac5_other_users_interview_forbidden(client, db_session):
    await _signup_and_login(client, email="owner3@example.com")
    other_token = await _signup_and_login(client, email="other3@example.com")
    interview = await _make_interview(db_session, candidate_email="owner3@example.com")

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(other_token),
        json={"language": "python", "code": "print(1)"},
    )
    assert resp.status_code == 403


async def test_ac6_unsupported_language_returns_422(client, db_session):
    """2026-09-09 갱신 — JavaScript는 이제 지원 언어라 이 테스트에서 뺐다
    (아래 test_js_* 참조). 스키마 자체(Literal["python", "javascript"])가
    그 외 값을 422로 막는지만 확인."""
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "ruby", "code": "puts 1"},
    )
    assert resp.status_code == 422


async def test_ac7_syntax_error_returns_stderr_not_500(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "python", "code": "def f(:\n    pass"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["exit_code"] != 0
    assert "SyntaxError" in body["stderr"]


# --- JavaScript 지원(2026-09-09, REQ-F-004 갭 해소) ---
@pytestmark_js
async def test_js_ac1_normal_code_executes_successfully(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "javascript", "code": "console.log('hi')"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "hi" in body["stdout"]
    assert body["exit_code"] == 0
    assert body["timed_out"] is False


@pytestmark_js
async def test_js_ac2_infinite_loop_times_out(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "javascript", "code": "while (true) {}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["timed_out"] is True


@pytestmark_js
async def test_js_ac3_app_secrets_not_leaked_to_child_process(client, db_session, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "super-secret-value-should-not-leak")

    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "javascript", "code": "console.log(JSON.stringify(process.env))"},
    )
    assert resp.status_code == 201
    stdout = resp.json()["stdout"]
    assert "should-not-leak" not in stdout
    assert "JWT_SECRET" not in stdout


@pytestmark_js
async def test_js_ac7_syntax_error_returns_stderr_not_500(client, db_session):
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "javascript", "code": "function f( {"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["exit_code"] != 0
    assert body["stderr"]
