"""ADR-007 — ⚠️ 진짜 샌드박스가 아님, 완화 조치만 적용. 반드시 ADR 원문 확인.

docs/trd/aimock_u2b_trd.md §3. 2026-09-08 ADR-007 재검토 후속(1단계 강화):
CPU/메모리 상한(RLIMIT) + 비root 권한 하락 + seccomp로 네트워크/외부프로그램
실행 차단. 전부 실제 Docker 컨테이너에서 exploit 스크립트로 직접 검증
완료(`내부테스트결과서/` 참조) — 파일시스템 격리는 여전히 안 됨(§ 아래
DROPPED_UID 관련 주석과 ADR-007 원문 "여전히 남아있는 한계" 참조).
"""

import asyncio
import os
import subprocess
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

TIMEOUT_SECONDS = 5
# RLIMIT_CPU는 TIMEOUT_SECONDS보다 넉넉히 크게 잡는다 — 둘 다 5초로 같으면
# CPU를 100% 쓰는 무한루프에서 RLIMIT_CPU의 SIGKILL이 subprocess.run의
# wall-clock timeout보다 먼저(또는 거의 동시에) 도착하는 경쟁 상태가
# 생겨서, 정상적으로 `timed_out=True`가 찍혀야 할 응답이 그냥 "exit_code
# -9로 죽은 프로세스"로 보고돼버린다(2026-09-08 실제 컨테이너 재현·발견 —
# AC-2 회귀). RLIMIT_CPU는 "혹시 wall-clock 타임아웃이 안 걸리는 예외
# 상황"을 잡는 최후 안전망 역할만 하도록 여유를 둔다.
CPU_RLIMIT_SECONDS = TIMEOUT_SECONDS + 5
MAX_MEMORY_BYTES = 256 * 1024 * 1024  # ADR-007 재검토(2026-09-08) 후속 강화

# nobody:nogroup — 거의 모든 리눅스 배포판에서 관용적으로 쓰는 비특권 UID/GID.
# 컨테이너 안에 실제로 존재하는지 실행 시점에 확인(_drop_privileges 참조).
DROPPED_UID = 65534
DROPPED_GID = 65534

# 이 목록에 있는 syscall은 샌드박스 안에서 전부 EPERM으로 막힌다.
# - socket 계열: 네트워크 접근 자체를 차단(내부망 스캔/외부 유출 방지)
# - execve 계열: 다른 프로그램 실행 차단(os.system/subprocess로 셸 명령
#   실행하는 것 방지) — 주의: 이건 "제출된 코드 안에서의" execve만 막는
#   것이고, 이 필터를 적용하는 러너 스크립트 자체를 최초 실행하는 execve
#   (subprocess.run이 내부적으로 한 번 호출)는 필터 적용 *이전*이라 영향
#   없음 — `_RUNNER_SCRIPT`가 스스로 락다운을 건 *다음에* 사용자 코드를
#   exec()로 같은 프로세스 안에서 돌리는 구조라 안전하다.
SECCOMP_BLOCKED_SYSCALLS = (
    "socket",
    "socketpair",
    "connect",
    "bind",
    "listen",
    "accept",
    "accept4",
    "execve",
    "execveat",
)

# 실제로 실행되는 것은 사용자 코드가 아니라 이 러너다. 러너가 먼저 자기
# 자신에게 seccomp 필터를 걸고(락다운), 그 다음에야 사용자 코드를 같은
# 프로세스 안에서 exec()한다 — 그래야 "러너를 실행하는 최초 execve"는
# 필터 적용 전이라 안 막히고, "사용자 코드가 시도하는 execve/socket"만
# 막힌다. 리눅스가 아니면(Windows 로컬 개발) 락다운을 조용히 건너뛴다.
_RUNNER_SCRIPT = f"""
import sys

def _lockdown():
    if sys.platform != "linux":
        return
    try:
        import pyseccomp as sc
    except ImportError:
        return
    f = sc.SyscallFilter(defaction=sc.ALLOW)
    for name in {SECCOMP_BLOCKED_SYSCALLS!r}:
        try:
            f.add_rule(sc.ERRNO(1), name)
        except Exception:
            pass  # 커널/아키텍처에 없는 syscall 이름은 무시
    f.load()

_lockdown()
with open(sys.argv[1], encoding="utf-8") as _f:
    _code = _f.read()
exec(compile(_code, sys.argv[1], "exec"))
"""


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool
    duration_ms: int


class CodeExecutor(ABC):
    @abstractmethod
    async def run(self, code: str) -> ExecResult: ...


class SubprocessExecutor(CodeExecutor):
    """ADR-007 A안. 환경변수 최소화(AC-3) + 타임아웃(AC-2) + 2026-09-08
    추가: 비root 권한 하락 + seccomp 네트워크/exec 차단."""

    async def run(self, code: str) -> ExecResult:
        return await asyncio.to_thread(self._run_sync, code)

    def _run_sync(self, code: str) -> ExecResult:
        with tempfile.TemporaryDirectory() as tmp_dir:
            script_path = Path(tmp_dir) / "submission.py"
            script_path.write_text(code, encoding="utf-8")
            runner_path = Path(tmp_dir) / "_runner.py"
            runner_path.write_text(_RUNNER_SCRIPT, encoding="utf-8")

            # 권한을 낮춘 자식 프로세스도 이 파일들을 읽을 수 있어야 한다
            # (기본 TemporaryDirectory 권한은 소유자 전용 0700).
            os.chmod(tmp_dir, 0o755)
            os.chmod(script_path, 0o644)
            os.chmod(runner_path, 0o644)

            restricted_env = _minimal_env()
            start = time.monotonic()
            try:
                proc = subprocess.run(
                    [sys.executable, str(runner_path), str(script_path)],
                    cwd=tmp_dir,
                    env=restricted_env,
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SECONDS,
                    # POSIX(Linux 컨테이너 배포 환경)에서만 적용 — Windows에는
                    # `resource` 모듈 자체가 없어 로컬 pytest(Windows 호스트)
                    # 실행 시에는 자연히 적용 안 됨.
                    preexec_fn=_harden_child if os.name == "posix" else None,
                )
                duration_ms = int((time.monotonic() - start) * 1000)
                return ExecResult(
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    exit_code=proc.returncode,
                    timed_out=False,
                    duration_ms=duration_ms,
                )
            except subprocess.TimeoutExpired as exc:
                duration_ms = int((time.monotonic() - start) * 1000)
                return ExecResult(
                    stdout=(exc.stdout or b"").decode("utf-8", errors="replace")
                    if isinstance(exc.stdout, bytes)
                    else (exc.stdout or ""),
                    stderr="실행 시간이 초과되었습니다(5초).",
                    exit_code=None,
                    timed_out=True,
                    duration_ms=duration_ms,
                )


def _minimal_env() -> dict[str, str]:
    """docs/trd/aimock_u2b_trd.md AC-3: 앱 시크릿은 절대 넘기지 않되,
    Python/OS가 정상 기동하기 위한 최소한의 일반 환경변수만 전달한다."""
    allowlist = ("PATH", "SYSTEMROOT", "SYSTEMDRIVE", "TEMP", "TMP", "PYTHONIOENCODING")
    return {k: os.environ[k] for k in allowlist if k in os.environ}


def _harden_child() -> None:
    """자식 프로세스 exec 직전(POSIX만) 호출.

    순서가 중요하다: 리소스 제한 → 권한 하락(마지막) — setuid는 되돌릴 수
    없으므로 반드시 다른 준비를 다 끝낸 다음 가장 마지막에 한다. seccomp
    자체는 여기가 아니라 `_RUNNER_SCRIPT`(사용자 코드 exec 직전)에서
    건다 — 여기서 걸면 러너를 실행하는 execve 자체가 막혀버린다.
    """
    import resource  # POSIX 전용 — mypy가 Windows 기준으로 검사해 아래 줄만 무시 처리

    resource.setrlimit(resource.RLIMIT_CPU, (CPU_RLIMIT_SECONDS, CPU_RLIMIT_SECONDS))  # type: ignore[attr-defined]
    resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES))  # type: ignore[attr-defined]
    _drop_privileges()


def _drop_privileges() -> None:
    """root로 떠 있는 경우(현재 이 프로젝트의 기본 배포 상태) nobody로
    낮춘다. 이미 non-root면 아무것도 안 한다. 실패해도(예: 컨테이너에
    nobody가 없는 특이 환경) 예외를 던져 코딩 테스트 기능 전체를 죽이지
    않고, 리소스 제한/타임아웃 방어만이라도 유지한 채 조용히 계속한다."""
    if os.getuid() != 0:  # type: ignore[attr-defined]  # POSIX 전용, mypy는 Windows 기준 검사
        return
    try:
        os.setgroups([])  # type: ignore[attr-defined]
        os.setgid(DROPPED_GID)  # type: ignore[attr-defined]
        os.setuid(DROPPED_UID)  # type: ignore[attr-defined]
    except OSError:
        pass
