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
    db: AsyncSession,
    category: str | None = None,
    difficulty: int | None = None,
    limit: int = 3,
    exclude_contents: list[str] | None = None,
) -> list[Question]:
    """`exclude_contents`: 2026-09-08 추가 — 이미 이번 면접에서 나온 질문을
    다시 후보로 뽑지 않기 위함. 실사용 중 "AI가 똑같은 질문을 계속
    반복한다"는 문제를 발견했는데, 원인은 이 함수가 매 턴 전체 질문은행
    에서 무작위로 뽑다 보니 같은 질문이 다시 뽑히고, LLM이 후보를 거의
    그대로 다시 질문해버리는 것이었다(실제 Groq 응답으로 재현·확인,
    `내부테스트결과서/` 참조 — LLM 제공자 문제가 아니라 이 함수의 설계
    문제였음)."""
    stmt = select(Question)
    if category:
        stmt = stmt.where(Question.category == category)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if exclude_contents:
        stmt = stmt.where(Question.content.notin_(exclude_contents))
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
