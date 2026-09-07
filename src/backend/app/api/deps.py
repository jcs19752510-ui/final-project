from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotAuthenticatedError
from app.core.security import decode_access_token
from app.db import get_db
from app.models.user import User
from app.sandbox.executor import CodeExecutor, SubprocessExecutor
from app.services.user_service import get_active_user

_bearer = HTTPBearer(auto_error=False)
_code_executor: CodeExecutor = SubprocessExecutor()


def get_code_executor() -> CodeExecutor:
    return _code_executor


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise NotAuthenticatedError("인증 토큰이 필요합니다.")

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise NotAuthenticatedError("유효하지 않은 토큰입니다.")

    user = await get_active_user(db, user_id)
    if user is None:
        # 탈퇴(소프트삭제)된 계정이면 즉시 401 (TRD U1 AC-5)
        raise NotAuthenticatedError("계정을 찾을 수 없습니다.")
    return user


async def require_recruiter(current_user: User = Depends(get_current_user)) -> User:
    """docs/trd/aimock_u5_trd.md §0-1: recruiter만 대시보드 접근 가능."""
    if current_user.role != "recruiter":
        raise ForbiddenError("채용담당자만 접근할 수 있습니다.")
    return current_user
