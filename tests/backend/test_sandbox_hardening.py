"""ADR-007 재검토(2026-09-08, 1단계 강화) — 실제 exploit 스타일 페이로드로
seccomp/권한하락이 진짜로 막는지 검증. `app/sandbox/executor.py`를 HTTP/DB
없이 직접 호출(단위 테스트 수준).

seccomp는 리눅스 전용이라 Windows 로컬 실행 시에는 스킵된다 — 실제 배포
환경(Docker/Linux)에서 `docker compose exec app pytest tests/backend/test_sandbox_hardening.py -v`
로 재확인 완료(내부테스트결과서 참조).
"""

import sys

import pytest

from app.sandbox.executor import SubprocessExecutor

pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="seccomp 네트워크/exec 차단은 리눅스 컨테이너에서만 동작"
)


async def test_normal_code_still_works_with_hardening():
    result = await SubprocessExecutor().run("print(1 + 1)")
    assert result.exit_code == 0
    assert "2" in result.stdout


async def test_socket_creation_is_blocked():
    code = (
        "import socket\n"
        "try:\n"
        "    socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "    print('SOCKET_SUCCEEDED')\n"
        "except OSError as e:\n"
        "    print('SOCKET_BLOCKED', e)\n"
    )
    result = await SubprocessExecutor().run(code)
    assert "SOCKET_BLOCKED" in result.stdout
    assert "SOCKET_SUCCEEDED" not in result.stdout


async def test_subprocess_exec_is_blocked():
    code = (
        "import subprocess\n"
        "try:\n"
        "    subprocess.run(['whoami'], capture_output=True, timeout=3)\n"
        "    print('EXEC_SUCCEEDED')\n"
        "except Exception as e:\n"
        "    print('EXEC_BLOCKED', type(e).__name__)\n"
    )
    result = await SubprocessExecutor().run(code)
    assert "EXEC_BLOCKED" in result.stdout
    assert "EXEC_SUCCEEDED" not in result.stdout


async def test_os_system_shell_command_is_blocked():
    code = "import os\nret = os.system('whoami')\nprint('RET', ret)\n"
    result = await SubprocessExecutor().run(code)
    # os.system은 내부적으로 /bin/sh -c "..."를 execve하므로, execve가
    # 막히면 셸 자체를 못 띄워 0이 아닌(보통 127<<8) 리턴코드가 찍힌다.
    assert "RET 0" not in result.stdout


async def test_runs_as_non_root_when_started_as_root():
    import os as os_module

    if os_module.getuid() != 0:
        pytest.skip("이 프로세스 자체가 root가 아니라 권한 하락 여부를 검증할 수 없음")
    code = "import os\nprint('UID', os.getuid())\n"
    result = await SubprocessExecutor().run(code)
    assert "UID 0" not in result.stdout
    assert "UID 65534" in result.stdout
