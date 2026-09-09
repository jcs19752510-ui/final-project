"""2026-09-09 보안 강화 — 99.모의면접_전수검사/전수검사결과_20260909101218.md
F-1(JWT 기본값 무방비)/F-10(업로드 검증 부재) 조치에 대한 회귀 테스트.
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "src" / "backend"


def _run_config_import(jwt_secret: str) -> subprocess.CompletedProcess:
    """`app.config` 임포트만 하는 별도 프로세스를 띄운다 — 현재 테스트
    프로세스에는 이미 정상 시크릿으로 임포트된 `app.config` 싱글턴이
    떠 있어서, 같은 프로세스 안에서 `importlib.reload`로 실패 케이스를
    흉내내면 그 싱글턴이 깨져 이후 다른 테스트가 전부 오염된다 — 그래서
    완전히 독립된 서브프로세스로 검증한다."""
    env = {**os.environ, "JWT_SECRET": jwt_secret}
    return subprocess.run(
        [sys.executable, "-c", "import app.config"],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_f1_jwt_secret_default_prevents_app_from_starting():
    """F-1 — JWT_SECRET이 공개된 기본값 그대로면 앱이 아예 기동하지 않아야
    한다(fail-fast). 인증 서명 키가 알려진 문자열이면, 누구든 그 문자열로
    유효한 토큰을 위조할 수 있어 인증 시스템 전체가 무력화된다."""
    result = _run_config_import("dev-only-secret-change-me")
    assert result.returncode != 0
    assert "JWT_SECRET" in result.stderr


def test_f1_jwt_secret_real_value_starts_normally():
    """대조군 — 실제(기본값이 아닌) 시크릿이면 정상적으로 임포트된다.
    F-1 조치가 과도해서 정상 배포까지 막는 회귀가 없는지 확인."""
    result = _run_config_import("an-actual-random-secret-value-not-the-default")
    assert result.returncode == 0, result.stderr


async def _signup_and_login(client, email="secfix@example.com"):
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


async def test_f10_oversized_file_rejected_with_413(client, monkeypatch):
    """F-10 — 파일 크기 상한을 넘으면 413로 거절되고 저장되지 않아야 한다.
    실제로 25MB짜리 파일을 만들어 보내면 테스트가 느려지므로, 상한 자체를
    낮춰서(monkeypatch) 작은 페이로드로도 검증한다."""
    from app.services import media_service

    monkeypatch.setattr(media_service, "MAX_UPLOAD_FILE_BYTES", 10)

    token = await _signup_and_login(client)
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/media",
        headers=_auth(token),
        data={"kind": "video_frame", "turn_index": "0"},
        files={"file": ("frame.jpg", b"this-is-longer-than-ten-bytes", "image/jpeg")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


async def test_f10_mismatched_content_type_rejected_with_415(client):
    """F-10 — kind="audio"인데 content-type이 이미지면 거절해야 한다."""
    token = await _signup_and_login(client, email="secfix2@example.com")
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/media",
        headers=_auth(token),
        data={"kind": "audio", "turn_index": "0"},
        files={"file": ("frame.jpg", b"not-actually-audio", "image/jpeg")},
    )
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


async def test_f10_invalid_kind_value_rejected(client):
    """F-10 — kind가 audio/video_frame이 아니면 FastAPI Literal 검증(422)
    또는 서비스 계층 검증(415) 둘 중 하나로 반드시 막혀야 한다(어느 쪽이든
    저장은 절대 되면 안 됨이 핵심)."""
    token = await _signup_and_login(client, email="secfix3@example.com")
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/media",
        headers=_auth(token),
        data={"kind": "not_a_real_kind", "turn_index": "0"},
        files={"file": ("x.bin", b"whatever", "application/octet-stream")},
    )
    assert resp.status_code in (415, 422)


async def test_f10_valid_audio_upload_still_works(client):
    """회귀 방지 — 정상적인 audio/webm 업로드는 F-10 조치 이후에도 그대로
    성공해야 한다(과도한 검증으로 정상 케이스를 막으면 안 됨)."""
    token = await _signup_and_login(client, email="secfix4@example.com")
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/media",
        headers=_auth(token),
        data={"kind": "audio", "turn_index": "0"},
        files={"file": ("turn.webm", b"fake-but-correctly-typed-audio", "audio/webm")},
    )
    assert resp.status_code == 201


async def test_f10_turn_submission_with_oversized_audio_rejected(client, monkeypatch, _fake_providers):
    """F-10이 media.py 직접 업로드 경로뿐 아니라 면접 턴 제출(U2-a) 경로에도
    적용되는지 확인 — 두 라우트가 결국 같은 `media_service.upload_media`를
    타므로 한 곳만 고치면 되지만, 실제로 그 경로까지 검증이 도달하는지는
    별도로 확인해야 한다(원본 우선/직접 검증 원칙)."""
    from app.services import media_service

    monkeypatch.setattr(media_service, "MAX_UPLOAD_FILE_BYTES", 10)

    token = await _signup_and_login(client, email="secfix5@example.com")
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        headers=_auth(token),
        data={"turn_index": "0"},
        files={"audio": ("a.webm", b"this-is-longer-than-ten-bytes-of-audio", "audio/webm")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


async def test_f10_global_middleware_rejects_declared_oversized_request(client, monkeypatch):
    """F-10 심화 — 개별 파일 검증(본문을 다 읽은 뒤 걸러짐)과는 별개로,
    Content-Length가 지나치게 큰 요청 자체를 앞단에서 거절하는 전역
    미들웨어가 실제로 동작하는지 확인."""
    import app.main as main_module

    # 회원가입/로그인/면접 시작 요청 자체도 이 임계값에 걸리지 않도록,
    # 먼저 정상 흐름을 다 마친 뒤에야 임계값을 낮춘다(그렇지 않으면 signup
    # 요청부터 413에 걸려 이 테스트가 애초에 성립하지 않음).
    token = await _signup_and_login(client, email="secfix6@example.com")
    start = await client.post(
        "/api/v1/interviews", headers=_auth(token), json={"job_role": "backend"}
    )
    interview_id = start.json()["interview_id"]

    monkeypatch.setattr(main_module, "_MAX_REQUEST_BODY_BYTES", 50)

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/media",
        headers=_auth(token),
        data={"kind": "video_frame", "turn_index": "0"},
        files={"file": ("frame.jpg", b"x" * 200, "image/jpeg")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
