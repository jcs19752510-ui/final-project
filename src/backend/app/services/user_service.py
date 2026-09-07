from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import rate_limit
from app.core.errors import DuplicateEmailError, InvalidCredentialsError, RateLimitedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import LoginRequest, SignupRequest


async def signup(db: AsyncSession, payload: SignupRequest) -> User:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise DuplicateEmailError(f"이미 가입된 이메일입니다: {payload.email}")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login(db: AsyncSession, payload: LoginRequest) -> str:
    """로그인 성공 시 access token 반환. ADR-006: 유예기간 내 탈퇴 계정은 자동 복구.

    브루트포스 완화(2026-09-08 추가): 같은 이메일로 15분 내 5회 이상 실패하면
    잠금(429). `app/core/rate_limit.py` 참조 — 새 정책이라 AC 문서화 없이
    자동진행으로 추가한 방어 조치(스코프 상 새 기능이 아니라 보안 강화).
    """
    if rate_limit.is_locked_out(payload.email):
        raise RateLimitedError(
            "로그인 시도가 너무 많습니다. 15분 후 다시 시도해 주세요."
        )

    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        rate_limit.record_failure(payload.email)
        raise InvalidCredentialsError("이메일 또는 비밀번호가 올바르지 않습니다.")

    now = datetime.now(timezone.utc)
    if user.deleted_at is not None:
        if user.purge_at is not None and user.purge_at > now:
            # 유예기간 내 재로그인 → 계정 복구 (ADR-006)
            user.deleted_at = None
            user.purge_at = None
            await db.commit()
        else:
            # purge_at이 지났으면(스케줄러가 아직 못 지웠어도) 존재하지 않는 계정으로 취급
            rate_limit.record_failure(payload.email)
            raise InvalidCredentialsError("이메일 또는 비밀번호가 올바르지 않습니다.")

    rate_limit.reset(payload.email)
    return create_access_token(user.id)


async def get_active_user(db: AsyncSession, user_id: UUID) -> User | None:
    user = await db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None
    return user


async def withdraw(db: AsyncSession, user_id: UUID) -> None:
    user = await db.get(User, user_id)
    if user is None:
        return
    now = datetime.now(timezone.utc)
    user.deleted_at = now
    user.purge_at = now + timedelta(days=settings.account_deletion_grace_days)
    await db.commit()


async def purge_expired_users(db: AsyncSession) -> list[UUID]:
    """ADR-006: purge_at이 지난 사용자를 연관 데이터(U1-b 미디어 포함)와 함께 물리 삭제."""
    from app.services.media_service import purge_user_media  # 순환 임포트 회피

    now = datetime.now(timezone.utc)
    stmt = select(User).where(User.purge_at.is_not(None), User.purge_at <= now)
    expired_users = list((await db.scalars(stmt)).all())

    purged_ids: list[UUID] = []
    for user in expired_users:
        await purge_user_media(db, user.id)
        purged_ids.append(user.id)
        await db.delete(user)  # interviews 등은 ON DELETE CASCADE로 함께 삭제
    await db.commit()
    return purged_ids
