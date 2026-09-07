"""로그인 브루트포스 완화 — 이메일당 실패 시도 슬라이딩 윈도우(인메모리).

ADR-003(Redis 미도입)·ADR-005(단일 Docker Compose 인스턴스, 수평확장 없음)
결정과 일치하는 인메모리 구현. 여러 인스턴스로 수평확장하게 되면 이 상태를
공유 저장소로 옮겨야 한다(그때 재검토).
"""

import time

MAX_FAILED_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60

_failed_attempts: dict[str, list[float]] = {}


def is_locked_out(email: str) -> bool:
    key = email.lower()
    now = time.monotonic()
    recent = [t for t in _failed_attempts.get(key, []) if now - t < WINDOW_SECONDS]
    _failed_attempts[key] = recent
    return len(recent) >= MAX_FAILED_ATTEMPTS


def record_failure(email: str) -> None:
    key = email.lower()
    _failed_attempts.setdefault(key, []).append(time.monotonic())


def reset(email: str) -> None:
    _failed_attempts.pop(email.lower(), None)
