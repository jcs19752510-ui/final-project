from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotAuthenticatedError
from app.core.security import decode_access_token
from app.db import get_db
from app.models.user import User
from app.services.user_service import get_active_user

_bearer = HTTPBearer(auto_error=False)


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
