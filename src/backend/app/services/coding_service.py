"""docs/trd/aimock_u2b_trd.md §3."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.models.coding_submission import CodingSubmission
from app.models.interview import Interview
from app.sandbox.executor import CodeExecutor, ExecResult

# 2026-09-09(전수검사결과_20260909101218.md REQ-F-004): 원안(PDF)이
# Python+JavaScript 2개 언어를 요구했는데 Python만 지원하던 갭을 해소.
SUPPORTED_LANGUAGES = {"python", "javascript"}


class UnsupportedLanguageError(AppError):
    status_code = 422
    code = "UNSUPPORTED_LANGUAGE"


async def submit_code(
    db: AsyncSession,
    interview_id: UUID,
    user_id: UUID,
    language: str,
    code: str,
    executor: CodeExecutor,
) -> tuple[CodingSubmission, ExecResult]:
    if language not in SUPPORTED_LANGUAGES:
        raise UnsupportedLanguageError(
            f"지원하지 않는 언어입니다: {language} (지원 언어: {sorted(SUPPORTED_LANGUAGES)})"
        )

    interview = await db.get(Interview, interview_id)
    if interview is None:
        raise NotFoundError("면접 세션을 찾을 수 없습니다.")
    if interview.candidate_id != user_id:
        raise ForbiddenError("본인 소유의 면접 세션이 아닙니다.")

    result = await executor.run(code, language)

    submission = CodingSubmission(
        interview_id=interview_id,
        language=language,
        code=code,
        exec_result_json={
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "duration_ms": result.duration_ms,
        },
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission, result
