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


# --- JavaScript(Node) 샌드박스(2026-09-09) ---
# 모듈 docstring(app/sandbox/executor.py) 참조: JS는 Python과 달리
# seccomp(네트워크/exec 차단)를 적용하지 않기로 사용자가 승인했다 — 아래
# 테스트는 "리소스 제한은 JS에도 적용된다"와 "네트워크는 실제로 안
# 막힌다(알려진 한계를 회귀 테스트로 고정)"를 둘 다 확인한다.
import shutil

_HAS_NODE = shutil.which("node") is not None
pytestmark_js = pytest.mark.skipif(
    not _HAS_NODE, reason="node 미설치 환경(Windows 로컬 등) — Linux 컨테이너에서만 확인"
)


@pytestmark_js
async def test_js_normal_code_works():
    result = await SubprocessExecutor().run("console.log(1 + 1);", language="javascript")
    assert result.exit_code == 0
    assert "2" in result.stdout


@pytestmark_js
async def test_js_infinite_loop_times_out():
    result = await SubprocessExecutor().run("while (true) {}", language="javascript")
    assert result.timed_out is True


@pytestmark_js
async def test_js_runs_as_non_root_when_started_as_root():
    import os as os_module

    if os_module.getuid() != 0:
        pytest.skip("이 프로세스 자체가 root가 아니라 권한 하락 여부를 검증할 수 없음")
    result = await SubprocessExecutor().run("console.log('UID', process.getuid());", language="javascript")
    assert "UID 0" not in result.stdout
    assert "UID 65534" in result.stdout


@pytestmark_js
async def test_js_network_access_is_not_blocked_known_gap():
    """⚠️ 이건 "정상 동작"을 확인하는 게 아니라 **알려진 보안 한계를
    문서화·고정**하는 회귀 테스트다. Python 경로(위 test_socket_creation_is_blocked)
    와 정확히 대칭되는 코드를 JS로 실행했을 때, socket 생성이 (seccomp가
    없으므로) 성공해야 정상이다 — 만약 나중에 이 테스트가 실패한다면
    (SOCKET_BLOCKED가 나온다면) 그건 이 프로젝트 문서(ADR-007, 사용자
    매뉴얼)의 "JS는 네트워크 차단 안 됨" 설명이 더 이상 사실과 다르다는
    뜻이니 문서를 갱신해야 한다."""
    code = (
        "const net = require('net');\n"
        "try {\n"
        "  const s = net.createConnection({host: '127.0.0.1', port: 1, timeout: 100});\n"
        "  s.on('error', () => console.log('CONNECT_ATTEMPTED_AND_FAILED_FOR_OTHER_REASON'));\n"
        "  console.log('SOCKET_CREATION_SUCCEEDED');\n"
        "} catch (e) {\n"
        "  console.log('SOCKET_BLOCKED', e.message);\n"
        "}\n"
    )
    result = await SubprocessExecutor().run(code, language="javascript")
    assert "SOCKET_CREATION_SUCCEEDED" in result.stdout
    assert "SOCKET_BLOCKED" not in result.stdout
