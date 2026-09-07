"""docs/trd/aimock_u2b_trd.md §5/§6. 실제 subprocess로 실행(mock 없음)."""

from sqlalchemy import select

from app.models.coding_submission import CodingSubmission
from app.models.interview import Interview
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
    token = await _signup_and_login(client)
    interview = await _make_interview(db_session)

    resp = await client.post(
        f"/api/v1/interviews/{interview.id}/coding-submissions",
        headers=_auth(token),
        json={"language": "javascript", "code": "console.log(1)"},
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
