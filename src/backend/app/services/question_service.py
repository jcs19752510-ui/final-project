"""aimock_u3a_trd.md §2/§3. MVP: 임베딩 벡터검색 대신 category/difficulty 필터(§7 미결)."""

import random
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.seed.questions_seed import SAMPLE_QUESTIONS

DEFAULT_OPENING_QUESTION = "자기소개를 부탁드립니다."


async def seed_if_empty(db: AsyncSession) -> None:
    count = await db.scalar(select(func.count()).select_from(Question))
    if count:
        return
    for item in SAMPLE_QUESTIONS:
        db.add(Question(**item))
    await db.commit()


async def retrieve_candidates(
    db: AsyncSession, category: str | None = None, difficulty: int | None = None, limit: int = 3
) -> list[Question]:
    stmt = select(Question)
    if category:
        stmt = stmt.where(Question.category == category)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    rows = list((await db.scalars(stmt)).all())
    random.shuffle(rows)
    return rows[:limit]


async def pick_opening_question(db: AsyncSession, job_role: str) -> tuple[str, UUID | None]:
    candidates = await retrieve_candidates(db, category="general", difficulty=1, limit=1)
    if not candidates:
        candidates = await retrieve_candidates(db, category=job_role, limit=1)
    if candidates:
        return candidates[0].content, candidates[0].id
    return DEFAULT_OPENING_QUESTION, None
