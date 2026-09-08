"""docs/trd/aimock_u4_trd.md §3/§3-1.

2026-09-08: 리포트 생성을 동기 처리에서 백그라운드 처리로 전환(§3-1) —
운영 환경에서 1분 이상 걸리던 문제를 원래 설계 의도(마스터 TRD 아키텍처
다이어그램의 "BackgroundTasks로 비동기 처리")대로 바로잡은 것.
`start_report_generation`(요청 처리 세션에서 빠르게 실행)과
`run_report_generation`(백그라운드에서 독립 세션으로 실행)으로 분리한다.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.emotion import EmotionAnalyzer
from app.ai.prosody import ProsodyAnalyzer
from app.ai.report import ReportContext, ReportGenerator
from app.core.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from app.db import AsyncSessionLocal
from app.models.coding_submission import CodingSubmission
from app.models.evaluation_report import EvaluationReport
from app.models.interview import Interview
from app.models.media_asset import MediaAsset
from app.models.transcript import Transcript
from app.services import keyword_extractor, media_service

logger = logging.getLogger("aimock.report")

# 백그라운드 작업이 서버 재시작 등으로 중간에 죽어도 "생성 중"에 영원히
# 멈추지 않도록, 이 시간이 지난 processing은 재시도를 허용한다.
# aimock_u4_trd.md §3-1 — 로컬 실측(내부테스트결과서) 기준 전체 파이프라인이
# 몇 초~수십 초 수준이라 5분이면 넉넉한 여유.
PROCESSING_STALE_AFTER = timedelta(minutes=5)

GENERIC_FAILURE_MESSAGE = "리포트 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."


async def _get_owned_interview(db: AsyncSession, interview_id: UUID, user_id: UUID) -> Interview:
    interview = await db.get(Interview, interview_id)
    if interview is None:
        raise NotFoundError("면접 세션을 찾을 수 없습니다.")
    if interview.candidate_id != user_id:
        raise ForbiddenError("본인 소유의 면접 세션이 아닙니다.")
    return interview


def _is_stale(report: EvaluationReport) -> bool:
    if report.processing_started_at is None:
        return True  # 방어적 처리 — 이론상 processing인데 시각이 없으면 신뢰 못 함
    started = report.processing_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - started > PROCESSING_STALE_AFTER


async def _mark_processing(db: AsyncSession, report: EvaluationReport) -> None:
    report.status = "processing"
    report.processing_started_at = datetime.now(timezone.utc)
    report.error_message = None
    await db.commit()
    await db.refresh(report)


async def start_report_generation(
    db: AsyncSession, interview_id: UUID, user_id: UUID
) -> tuple[EvaluationReport, bool]:
    """리포트 생성을 "시작"만 한다 — 실제 무거운 작업은 하지 않음(요청 처리
    세션에서 빠르게 끝나야 함). 반환값의 두 번째 원소(`should_run`)가
    True일 때만 호출자(라우트)가 백그라운드 작업을 예약해야 한다 — 이미
    처리 중인 작업이 있으면 중복 실행하지 않기 위함(동시 두 번 클릭 등
    경합 상황 대응, u4 TRD §3-1).
    """
    interview = await _get_owned_interview(db, interview_id, user_id)
    if interview.status != "completed":
        raise ConflictError("완료된 면접만 리포트를 생성할 수 있습니다.")

    report = await db.scalar(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
    )

    if report is None:
        report = EvaluationReport(interview_id=interview_id, details_json={})
        db.add(report)
        try:
            await _mark_processing(db, report)
        except IntegrityError:
            # 동시에 두 요청이 동시에 "없음"을 보고 둘 다 insert를 시도한
            # 경쟁 상태 — 하나만 성공하고 나머지는 여기로 온다. 롤백 후
            # 방금 다른 요청이 만든 행을 다시 읽어 같은 로직(중복 실행
            # 방지)을 그대로 태운다.
            await db.rollback()
            report = await db.scalar(
                select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
            )
            assert report is not None  # noqa: S101 — 방금 유니크 충돌이 났으므로 반드시 존재
        else:
            return report, True

    if report.status == "processing" and not _is_stale(report):
        return report, False  # 이미 처리 중 — 중복 실행 방지, 새로 예약하지 않음

    await _mark_processing(db, report)
    return report, True


async def _fetch_report_row(db: AsyncSession, interview_id: UUID) -> EvaluationReport | None:
    return await db.scalar(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
    )


async def _build_emotion_timeline(
    db: AsyncSession, interview_id: UUID, analyzer: EmotionAnalyzer | None
) -> list[dict]:
    """docs/trd/aimock_u3b_trd.md §3. 라이브 웹캠 캡처 UI가 아직 없어
    `video_frame` 미디어가 없는 경우가 대부분 — 그때는 조용히 빈 배열."""
    if analyzer is None:
        return []
    frames = list(
        (
            await db.scalars(
                select(MediaAsset).where(
                    MediaAsset.interview_id == interview_id, MediaAsset.kind == "video_frame"
                )
            )
        ).all()
    )
    timeline = []
    for frame in frames:
        result = await analyzer.analyze_frame(media_service.read_media_bytes(frame))
        timeline.append(
            {
                "turn_index": frame.turn_index,
                "dominant_emotion": result.dominant_emotion,
                "confidence": result.confidence,
            }
        )
    return timeline


async def _build_voice_prosody(
    db: AsyncSession, interview_id: UUID, analyzer: ProsodyAnalyzer | None
) -> list[dict]:
    if analyzer is None:
        return []
    clips = list(
        (
            await db.scalars(
                select(MediaAsset).where(
                    MediaAsset.interview_id == interview_id, MediaAsset.kind == "audio"
                )
            )
        ).all()
    )
    prosody = []
    for clip in clips:
        result = await analyzer.analyze(media_service.read_media_bytes(clip))
        prosody.append(
            {
                "turn_index": clip.turn_index,
                "pitch_mean_hz": result.pitch_mean_hz,
                "energy_mean": result.energy_mean,
            }
        )
    return prosody


async def run_report_generation(
    interview_id: UUID,
    generator: ReportGenerator,
    emotion_analyzer: EmotionAnalyzer | None,
    prosody_analyzer: ProsodyAnalyzer | None,
) -> None:
    """FastAPI `BackgroundTasks`가 응답 전송 후 실행하는 실제 작업.

    요청 처리 세션(`get_db` 의존성)은 응답이 나갈 때 이미 닫히므로, 반드시
    **독립적인 새 세션**을 직접 열어야 한다(요청 세션을 재사용하면 이미
    닫힌 세션에 접근하는 버그가 된다 — FastAPI BackgroundTasks의 잘 알려진
    함정, u4 TRD §3-1에 명시).
    """
    async with AsyncSessionLocal() as db:
        try:
            interview = await db.get(Interview, interview_id)
            if interview is None:
                # interview가 그 사이 삭제됐다면 FK CASCADE로 report 행도
                # 이미 함께 삭제됐을 것 — 더 할 일 없음.
                return

            transcripts = list(
                (
                    await db.scalars(
                        select(Transcript)
                        .where(Transcript.interview_id == interview_id)
                        .order_by(Transcript.turn_index, Transcript.created_at)
                    )
                ).all()
            )
            submissions = list(
                (
                    await db.scalars(
                        select(CodingSubmission).where(
                            CodingSubmission.interview_id == interview_id
                        )
                    )
                ).all()
            )

            user_texts = [t.text for t in transcripts if t.speaker == "user"]
            keywords = keyword_extractor.extract(user_texts)

            context = ReportContext(
                job_role=interview.job_role,
                transcript_lines=[f"{t.speaker}: {t.text}" for t in transcripts],
                code_submissions=[s.code for s in submissions],
                keywords=keywords,
            )
            result = await generator.generate(context)
            emotion_timeline = await _build_emotion_timeline(db, interview_id, emotion_analyzer)
            voice_prosody = await _build_voice_prosody(db, interview_id, prosody_analyzer)

            report = await _fetch_report_row(db, interview_id)
            if report is None:
                logger.warning(
                    "리포트 행이 백그라운드 실행 중 사라짐(interview_id=%s) — 저장 건너뜀",
                    interview_id,
                )
                return

            report.technical_score = result.technical_score
            report.communication_score = result.communication_score
            report.cultural_fit_score = result.cultural_fit_score
            report.summary_text = result.summary_text
            report.details_json = {
                "star_analysis": result.star_analysis,
                "keywords": keywords,
                "pass_recommendation": result.pass_recommendation,
                "emotion_timeline": emotion_timeline,
                "voice_prosody": voice_prosody,
            }
            report.status = "completed"
            report.error_message = None
            await db.commit()
        except Exception as exc:  # noqa: BLE001 — 백그라운드 작업이라 예외를 밖으로 던져도 아무도 못 받음, 반드시 여기서 흡수하고 상태로 남겨야 함
            # 실패한 트랜잭션이 있을 수 있으니 롤백 후, 실패 표시는 별도
            # 커밋으로 분리(위 트랜잭션이 이미 깨졌을 가능성에 대비).
            await db.rollback()
            safe_message = exc.message if isinstance(exc, AppError) else GENERIC_FAILURE_MESSAGE
            logger.exception(
                "리포트 생성 실패(interview_id=%s), 사용자 노출 메시지: %s", interview_id, safe_message
            )
            report = await _fetch_report_row(db, interview_id)
            if report is not None:
                report.status = "failed"
                report.error_message = safe_message
                await db.commit()


async def get_report(db: AsyncSession, interview_id: UUID, user_id: UUID) -> EvaluationReport:
    await _get_owned_interview(db, interview_id, user_id)
    report = await db.scalar(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
    )
    if report is None:
        raise NotFoundError("아직 생성된 리포트가 없습니다.")
    return report
