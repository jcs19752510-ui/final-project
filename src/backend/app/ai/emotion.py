"""ADR-002/마스터 TRD 아키텍처: 표정 분석은 DeepFace 로컬 실행.
docs/trd/aimock_u3b_trd.md §2/§3.
"""

import asyncio
import logging
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("aimock.emotion")

UNKNOWN_EMOTION = "unknown"


@dataclass
class EmotionResult:
    dominant_emotion: str
    confidence: float  # 0.0~1.0


class EmotionAnalyzer(ABC):
    @abstractmethod
    async def analyze_frame(self, image_bytes: bytes) -> EmotionResult: ...


class DeepFaceEmotionAnalyzer(EmotionAnalyzer):
    """실제 구현. 얼굴 1장(이미지 바이트)을 받아 지배적 감정을 반환한다.

    docs/trd/aimock_u3b_trd.md AC-3: 얼굴이 검출되지 않아도 예외 대신
    `unknown` 폴백 — 리포트 생성 전체가 죽지 않게 격리.
    """

    def __init__(self, detector_backend: str = "opencv"):
        self._detector_backend = detector_backend

    async def analyze_frame(self, image_bytes: bytes) -> EmotionResult:
        return await asyncio.to_thread(self._analyze_sync, image_bytes)

    def _analyze_sync(self, image_bytes: bytes) -> EmotionResult:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_bytes)
            path = Path(f.name)
        try:
            from deepface import DeepFace

            results = DeepFace.analyze(
                img_path=str(path),
                actions=["emotion"],
                detector_backend=self._detector_backend,
                enforce_detection=True,
                silent=True,
            )
            # DeepFace는 얼굴이 여러 개면 리스트를 반환 — 첫 번째(가장 큰) 얼굴만 사용
            face = results[0] if isinstance(results, list) else results
            dominant = face["dominant_emotion"]
            confidence = float(face["emotion"][dominant]) / 100.0
            return EmotionResult(dominant_emotion=dominant, confidence=round(confidence, 4))
        except Exception as exc:  # noqa: BLE001 — 얼굴 미검출 등 DeepFace가 다양한 예외를 던짐
            logger.warning("표정 분석 실패, 폴백 사용: %s", exc)
            return EmotionResult(dominant_emotion=UNKNOWN_EMOTION, confidence=0.0)
        finally:
            path.unlink(missing_ok=True)
