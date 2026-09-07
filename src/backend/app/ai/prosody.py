"""ADR-002/마스터 TRD 아키텍처: 음성운율 분석은 librosa 로컬 실행.
docs/trd/aimock_u3b_trd.md §2/§3.
"""

import asyncio
import logging
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("aimock.prosody")


@dataclass
class ProsodyResult:
    pitch_mean_hz: float
    energy_mean: float


FALLBACK_RESULT = ProsodyResult(pitch_mean_hz=0.0, energy_mean=0.0)


class ProsodyAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, audio_bytes: bytes) -> ProsodyResult: ...


class LibrosaProsodyAnalyzer(ProsodyAnalyzer):
    """실제 구현. 피치(기본주파수) 평균과 에너지(RMS) 평균을 계산한다.

    docs/trd/aimock_u3b_trd.md §0-1: 분석 실패(무음, 디코딩 실패 등) 시
    예외 대신 폴백값 — 리포트 생성 전체가 죽지 않게 격리.
    """

    async def analyze(self, audio_bytes: bytes) -> ProsodyResult:
        return await asyncio.to_thread(self._analyze_sync, audio_bytes)

    def _analyze_sync(self, audio_bytes: bytes) -> ProsodyResult:
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as f:
            f.write(audio_bytes)
            path = Path(f.name)
        try:
            import librosa
            import numpy as np

            y, sr = librosa.load(str(path), sr=None, mono=True)
            if y.size == 0:
                return FALLBACK_RESULT

            f0, voiced_flag, _voiced_prob = librosa.pyin(
                y,
                fmin=float(librosa.note_to_hz("C2")),
                fmax=float(librosa.note_to_hz("C7")),
                sr=sr,
            )
            voiced_f0 = f0[voiced_flag] if f0 is not None else np.array([])
            pitch_mean = float(np.nanmean(voiced_f0)) if voiced_f0.size else 0.0
            if np.isnan(pitch_mean):
                pitch_mean = 0.0

            energy_mean = float(np.mean(librosa.feature.rms(y=y)))

            return ProsodyResult(
                pitch_mean_hz=round(pitch_mean, 2), energy_mean=round(energy_mean, 5)
            )
        except Exception as exc:  # noqa: BLE001 — 디코딩 실패 등 librosa/오디오 포맷 문제 폴백
            logger.warning("음성운율 분석 실패, 폴백 사용: %s", exc)
            return FALLBACK_RESULT
        finally:
            path.unlink(missing_ok=True)
