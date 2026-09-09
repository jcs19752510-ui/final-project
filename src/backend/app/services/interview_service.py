"""docs/trd/aimock_u2a_trd.md §3."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import ConversationContext, LLMProvider, LLMTurnResult
from app.ai.stt import STTProvider
from app.config import settings
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.interview import Interview
from app.models.question import Question
from app.models.transcript import Transcript
from app.services import media_service, question_service

logger = logging.getLogger("aimock.interview")

LENGTH_LIMIT_NOTICE = "답변이 길어지고 있어 다음 질문으로 넘어가겠습니다."
# ADR-008 연계(2026-09-08): 최소/최대 질문 개수는 LLM 프롬프트(§3)로도
# 안내하지만, 모델이 지시를 안 지켜도 서버가 최종적으로 강제한다(운영
# 환경에서 25턴 넘게 안 끝나는 문제를 실제로 발견해 추가한 안전장치).
CLOSING_MESSAGE = "여기까지 질문을 마치겠습니다. 답변해 주셔서 감사합니다. 수고하셨습니다."
EARLY_END_FALLBACK_QUESTION = (
    "조금 더 여쭤보고 싶습니다. 최근 진행한 프로젝트에서 가장 어려웠던 "
    "기술적 의사결정은 무엇이었고, 어떻게 해결하셨나요?"
)


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


def _enforce_question_count_bounds(
    result: LLMTurnResult, asked_count: int, candidates: list[Question]
) -> LLMTurnResult:
    """LLM이 프롬프트 지시(SYSTEM_PROMPT §진행 상황)를 안 따라도 서버가 최종
    강제한다. `asked_count`는 이번 응답 이전까지 이미 나온 질문 수(오프닝
    포함) — aimock_u2a_trd.md §3, ADR-008.
    """
    if result.action == "end_interview" and asked_count < settings.interview_min_questions:
        logger.info(
            "LLM이 최소 질문 수(%d) 미만(%d개)에서 종료를 시도해 서버가 계속 진행시킴",
            settings.interview_min_questions,
            asked_count,
        )
        fallback_text = candidates[0].content if candidates else EARLY_END_FALLBACK_QUESTION
        return LLMTurnResult(reply_text=fallback_text, action="ask_question", evaluation=result.evaluation)
    if result.action == "ask_question" and asked_count >= settings.interview_max_questions:
        logger.info(
            "LLM이 최대 질문 수(%d)를 넘겨 질문을 이어가려 해 서버가 강제 종료함",
            settings.interview_max_questions,
        )
        return LLMTurnResult(reply_text=CLOSING_MESSAGE, action="end_interview", evaluation=result.evaluation)
    return result


async def submit_turn(
    db: AsyncSession,
    interview_id: UUID,
    user_id: UUID,
    turn_index: int,
    audio_bytes: bytes,
    stt: STTProvider,
    llm: LLMProvider,
    content_type: str | None = None,
) -> tuple[str, bool]:
    interview = await _get_owned_live_interview(db, interview_id, user_id)

    # ADR-004(2026-09-07 확정): 원본 오디오는 지원자 삭제 요청 전까지 암호화
    # 보관해야 함 — 2026-09-08 재검토(마스터 TRD §3 N-003 라인 리뷰)에서
    # 이 흐름이 그동안 STT 변환에만 audio_bytes를 쓰고 U1-b 암호화 저장을
    # 호출하지 않는 것을 발견해 연결함(정책은 이미 승인됐고, 실행이
    # 누락됐던 것을 고친 것 — 새 정책 결정 아님).
    # 2026-09-09(F-10): content_type/크기 검증은 media_service.upload_media
    # 내부에서 일괄 처리(PayloadTooLargeError/UnsupportedMediaTypeError는
    # AppError라 라우트의 전역 핸들러가 알아서 413/415로 변환).
    await media_service.upload_media(
        db, interview.id, user_id, "audio", turn_index, audio_bytes, content_type=content_type
    )

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
    # 2026-09-08: 이미 이번 면접에서 나온 질문은 후보에서 제외 — 같은
    # 질문이 다시 뽑혀 LLM이 그걸 그대로 반복 질문하는 문제를 실제로
    # 발견해 수정(원인 상세는 question_service.retrieve_candidates 참조).
    already_asked = [h["text"] for h in history if h["speaker"] == "ai"]
    asked_count = len(already_asked)
    candidates = await question_service.retrieve_candidates(
        db, limit=3, exclude_contents=already_asked
    )
    context = ConversationContext(
        job_role=interview.job_role,
        history=history,
        candidate_questions=[q.content for q in candidates],
        question_number=asked_count + 1,
        min_questions=settings.interview_min_questions,
        max_questions=settings.interview_max_questions,
    )
    result = await llm.generate_next_turn(context)
    result = _enforce_question_count_bounds(result, asked_count, candidates)

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
