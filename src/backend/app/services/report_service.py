"""docs/trd/aimock_u4_trd.md §3."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.emotion import EmotionAnalyzer
from app.ai.prosody import ProsodyAnalyzer
from app.ai.report import ReportContext, ReportGenerator
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.coding_submission import CodingSubmission
from app.models.evaluation_report import EvaluationReport
from app.models.interview import Interview
from app.models.media_asset import MediaAsset
from app.models.transcript import Transcript
from app.services import keyword_extractor, media_service


async def _get_owned_interview(db: AsyncSession, interview_id: UUID, user_id: UUID) -> Interview:
    interview = await db.get(Interview, interview_id)
    if interview is None:
        raise NotFoundError("면접 세션을 찾을 수 없습니다.")
    if interview.candidate_id != user_id:
        raise ForbiddenError("본인 소유의 면접 세션이 아닙니다.")
    return interview


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


async def generate_report(
    db: AsyncSession,
    interview_id: UUID,
    user_id: UUID,
    generator: ReportGenerator,
    emotion_analyzer: EmotionAnalyzer | None = None,
    prosody_analyzer: ProsodyAnalyzer | None = None,
) -> EvaluationReport:
    interview = await _get_owned_interview(db, interview_id, user_id)
    if interview.status != "completed":
        raise ConflictError("완료된 면접만 리포트를 생성할 수 있습니다.")

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
                select(CodingSubmission).where(CodingSubmission.interview_id == interview_id)
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

    report = await db.scalar(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
    )
    if report is None:
        report = EvaluationReport(interview_id=interview_id)
        db.add(report)

    report.technical_score = result.technical_score
    report.communication_score = result.communication_score
    report.cultural_fit_score = result.cultural_fit_score
    report.summary_text = result.summary_text
    report.details_json = {
        "star_analysis": result.star_analysis,
        "keywords": keywords,
        "pass_recommendation": result.pass_recommendation,
        "emotion_timeline": emotion_timeline,  # U3-b: video_frame 미디어 없으면 빈 배열
        "voice_prosody": voice_prosody,
    }

    await db.commit()
    await db.refresh(report)
    return report


async def get_report(db: AsyncSession, interview_id: UUID, user_id: UUID) -> EvaluationReport:
    await _get_owned_interview(db, interview_id, user_id)
    report = await db.scalar(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
    )
    if report is None:
        raise NotFoundError("아직 생성된 리포트가 없습니다.")
    return report
