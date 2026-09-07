"""docs/trd/aimock_u2a_trd.md §3."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import ConversationContext, LLMProvider
from app.ai.stt import STTProvider
from app.config import settings
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.interview import Interview
from app.models.transcript import Transcript
from app.services import question_service

LENGTH_LIMIT_NOTICE = "답변이 길어지고 있어 다음 질문으로 넘어가겠습니다."


async def _get_owned_live_interview(db: AsyncSession, interview_id: UUID, user_id: UUID) -> Interview:
    interview = await db.get(Interview, interview_id)
    if interview is None:
        raise NotFoundError("면접 세션을 찾을 수 없습니다.")
    if interview.candidate_id != user_id:
        raise ForbiddenError("본인 소유의 면접 세션이 아닙니다.")
    if interview.status != "live":
        raise ConflictError("이미 종료된 면접입니다.")
    return interview


async def _get_owned_interview(db: AsyncSession, interview_id: UUID, user_id: UUID) -> Interview:
    interview = await db.get(Interview, interview_id)
    if interview is None:
        raise NotFoundError("면접 세션을 찾을 수 없습니다.")
    if interview.candidate_id != user_id:
        raise ForbiddenError("본인 소유의 면접 세션이 아닙니다.")
    return interview


async def start_interview(db: AsyncSession, user_id: UUID, job_role: str) -> tuple[Interview, str]:
    await question_service.seed_if_empty(db)

    interview = Interview(
        candidate_id=user_id, job_role=job_role, status="live", started_at=datetime.now(timezone.utc)
    )
    db.add(interview)
    await db.flush()

    question_text, question_id = await question_service.pick_opening_question(db, job_role)
    db.add(
        Transcript(
            interview_id=interview.id,
            question_id=question_id,
            turn_index=0,
            speaker="ai",
            text=question_text,
        )
    )
    await db.commit()
    await db.refresh(interview)
    return interview, question_text


async def _fetch_history(db: AsyncSession, interview_id: UUID) -> list[dict[str, str]]:
    stmt = (
        select(Transcript)
        .where(Transcript.interview_id == interview_id)
        .order_by(Transcript.turn_index, Transcript.created_at)
    )
    rows = list((await db.scalars(stmt)).all())
    return [{"speaker": r.speaker, "text": r.text} for r in rows]


async def submit_turn(
    db: AsyncSession,
    interview_id: UUID,
    user_id: UUID,
    turn_index: int,
    audio_bytes: bytes,
    stt: STTProvider,
    llm: LLMProvider,
) -> tuple[str, bool]:
    interview = await _get_owned_live_interview(db, interview_id, user_id)

    user_text = await stt.transcribe(audio_bytes)
    db.add(
        Transcript(interview_id=interview.id, turn_index=turn_index, speaker="user", text=user_text)
    )

    if len(user_text) > settings.turn_max_answer_chars:
        reply_text = LENGTH_LIMIT_NOTICE
        db.add(
            Transcript(
                interview_id=interview.id, turn_index=turn_index + 1, speaker="ai", text=reply_text
            )
        )
        await db.commit()
        return reply_text, False

    history = await _fetch_history(db, interview.id)
    history.append({"speaker": "user", "text": user_text})
    candidates = await question_service.retrieve_candidates(db, limit=3)
    context = ConversationContext(
        job_role=interview.job_role,
        history=history,
        candidate_questions=[q.content for q in candidates],
    )
    result = await llm.generate_next_turn(context)

    db.add(
        Transcript(
            interview_id=interview.id, turn_index=turn_index + 1, speaker="ai", text=result.reply_text
        )
    )
    ended = result.action == "end_interview"
    if ended:
        interview.status = "completed"
        interview.ended_at = datetime.now(timezone.utc)

    await db.commit()
    return result.reply_text, ended


async def end_interview(db: AsyncSession, interview_id: UUID, user_id: UUID) -> None:
    interview = await _get_owned_interview(db, interview_id, user_id)
    interview.status = "completed"
    interview.ended_at = datetime.now(timezone.utc)
    await db.commit()
