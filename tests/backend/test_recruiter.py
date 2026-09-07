"""docs/trd/aimock_u5_trd.md §5/§6."""

from sqlalchemy import select

from app.models.evaluation_report import EvaluationReport
from app.models.interview import Interview
from app.models.user import User


async def _signup_and_login(client, email, role="candidate"):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123", "role": role},
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login.json()["access_token"]


async def _make_completed_interview_with_report(
    db_session, candidate_email, technical=4, communication=4, cultural=3, pass_rec=True
) -> Interview:
    user = await db_session.scalar(select(User).where(User.email == candidate_email))
    interview = Interview(candidate_id=user.id, job_role="backend", status="completed")
    db_session.add(interview)
    await db_session.flush()
    db_session.add(
        EvaluationReport(
            interview_id=interview.id,
            technical_score=technical,
            communication_score=communication,
            cultural_fit_score=cultural,
            summary_text="요약",
            details_json={"pass_recommendation": pass_rec, "keywords": [], "emotion_timeline": []},
        )
    )
    await db_session.commit()
    await db_session.refresh(interview)
    return interview


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_ac1_recruiter_sees_all_candidates_interviews(client, db_session):
    await _signup_and_login(client, "cand1@example.com")
    await _signup_and_login(client, "cand2@example.com")
    recruiter_token = await _signup_and_login(client, "recruiter1@example.com", role="recruiter")

    await _make_completed_interview_with_report(db_session, "cand1@example.com")
    await _make_completed_interview_with_report(db_session, "cand2@example.com")

    resp = await client.get("/api/v1/recruiter/interviews", headers=_auth(recruiter_token))
    assert resp.status_code == 200
    emails = {row["candidate_email"] for row in resp.json()}
    assert emails == {"cand1@example.com", "cand2@example.com"}


async def test_ac2_candidate_forbidden_from_dashboard(client):
    candidate_token = await _signup_and_login(client, "cand3@example.com")

    for path in ["/api/v1/recruiter/interviews", "/api/v1/recruiter/stats"]:
        resp = await client.get(path, headers=_auth(candidate_token))
        assert resp.status_code == 403


async def test_ac3_recruiter_can_view_any_candidates_report(client, db_session):
    await _signup_and_login(client, "cand4@example.com")
    recruiter_token = await _signup_and_login(client, "recruiter2@example.com", role="recruiter")
    interview = await _make_completed_interview_with_report(db_session, "cand4@example.com")

    resp = await client.get(
        f"/api/v1/recruiter/interviews/{interview.id}/report", headers=_auth(recruiter_token)
    )
    assert resp.status_code == 200
    assert resp.json()["technical_score"] == 4


async def test_ac4_report_not_found_returns_404(client, db_session):
    user_token = await _signup_and_login(client, "cand5@example.com")
    recruiter_token = await _signup_and_login(client, "recruiter3@example.com", role="recruiter")

    # 리포트 없이 interview만 생성 (사용자 본인 API로 시작만 함)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(user_token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.get(
        f"/api/v1/recruiter/interviews/{interview_id}/report", headers=_auth(recruiter_token)
    )
    assert resp.status_code == 404


async def test_ac5_stats_average_is_correct(client, db_session):
    recruiter_token = await _signup_and_login(client, "recruiter4@example.com", role="recruiter")
    await _signup_and_login(client, "cand6@example.com")
    await _signup_and_login(client, "cand7@example.com")

    await _make_completed_interview_with_report(
        db_session, "cand6@example.com", technical=4, communication=4, cultural=3
    )
    await _make_completed_interview_with_report(
        db_session, "cand7@example.com", technical=5, communication=3, cultural=4
    )

    resp = await client.get("/api/v1/recruiter/stats", headers=_auth(recruiter_token))
    body = resp.json()
    assert body["completed_interviews"] == 2
    assert body["avg_technical_score"] == 4.5
    assert body["avg_communication_score"] == 3.5
    assert body["avg_cultural_fit_score"] == 3.5


async def test_ac6_no_token_returns_401(client):
    resp = await client.get("/api/v1/recruiter/interviews")
    assert resp.status_code == 401
