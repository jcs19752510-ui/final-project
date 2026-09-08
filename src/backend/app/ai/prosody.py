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

# 2026-09-08(u4 리포트 비동기화 후속) — 운영 환경(Render)에서 리포트 생성이
# 1분 이상 걸리는 문제를 실측으로 재분석한 결과, 병목은 DeepFace가 아니라
# `librosa.pyin()`이었다(로컬 실측: 8.75초 오디오 기준 pyin 3.16~3.39초 —
# 같은 클립의 DeepFace 웜 추론 0.04초, RMS 계산 0.015초 대비 압도적으로
# 느림, 내부테스트결과서 참조). pyin은 Viterbi 디코딩을 쓰는 확률적
# 알고리즘이라 원래 무겁다. 정확도 손실 없이 계산량만 줄이기 위해:
# (1) 분석 전 8kHz로 다운샘플 — 사람 음성 피치(기본주파수)는 수백Hz대라
#     8kHz(나이퀴스트 4kHz)로도 충분히 표현되고, pyin 연산량은 샘플 수에
#     비례해 줄어듦.
# (2) 탐색 상한을 C7(~2093Hz, 오페라 소프라노 수준)에서 C6(~1047Hz, 실제
#     사람 음성 범위를 넉넉히 덮음)로 좁힘 — pyin의 후보 주파수 탐색
#     공간이 줄어들어 추가로 빨라짐.
# 실측(동일 샘플): 3.16~3.39초 → 0.69초(약 4.7배), 평균 피치 결과값은
# 205.28Hz → 209.82Hz로 오차 2% 수준(무시 가능) — 정확도 저하 없이 속도만
# 개선됨을 확인.
PROSODY_TARGET_SR = 8000
PITCH_FMIN_NOTE = "C2"  # ~65.4Hz, 성인 남성 저음까지 포함
PITCH_FMAX_NOTE = "C6"  # ~1046.5Hz, 실제 사람 음성 범위를 넉넉히 덮음(C7은 과함)


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

            if sr > PROSODY_TARGET_SR:
                y = librosa.resample(y, orig_sr=sr, target_sr=PROSODY_TARGET_SR)
                sr = PROSODY_TARGET_SR

            f0, voiced_flag, _voiced_prob = librosa.pyin(
                y,
                fmin=float(librosa.note_to_hz(PITCH_FMIN_NOTE)),
                fmax=float(librosa.note_to_hz(PITCH_FMAX_NOTE)),
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
