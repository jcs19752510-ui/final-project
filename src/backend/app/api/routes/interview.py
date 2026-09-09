from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import LLMProvider
from app.ai.providers import get_llm_provider, get_stt_provider
from app.ai.stt import STTProvider
from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.interview import StartInterviewRequest, StartInterviewResponse, TurnResponse
from app.services import interview_service

router = APIRouter(prefix="/api/v1/interviews", tags=["interview"])


@router.post("", response_model=StartInterviewResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    payload: StartInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StartInterviewResponse:
    interview, question_text = await interview_service.start_interview(
        db, current_user.id, payload.job_role
    )
    return StartInterviewResponse(interview_id=interview.id, question_text=question_text)


@router.post("/{interview_id}/turns", response_model=TurnResponse)
async def submit_turn(
    interview_id: UUID,
    turn_index: int = Form(...),
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    stt: STTProvider = Depends(get_stt_provider),
    llm: LLMProvider = Depends(get_llm_provider),
) -> TurnResponse:
    raw = await audio.read()
    question_text, ended = await interview_service.submit_turn(
        db, interview_id, current_user.id, turn_index, raw, stt, llm, content_type=audio.content_type
    )
    return TurnResponse(question_text=question_text, ended=ended)


@router.post("/{interview_id}/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await interview_service.end_interview(db, interview_id, current_user.id)
