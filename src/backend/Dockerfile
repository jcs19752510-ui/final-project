FROM python:3.12-slim

WORKDIR /app

# U3-b(librosa)가 m4a 등 wav 이외 포맷을 디코딩할 때 필요(audioread 백엔드).
# faster-whisper(PyAV, 자체 번들)는 이거 없이도 이미 잘 됐지만 librosa의
# audioread 폴백 경로는 시스템 ffmpeg 바이너리를 직접 호출한다.
# libseccomp2: ADR-007 재검토(2026-09-08) — 코드 실행 샌드박스의 syscall
# 필터링(app/sandbox/executor.py)에 필요. ffmpeg 등이 우연히 딸려 설치해줄
# 수도 있지만 그 우연에 기대지 않고 명시적으로 설치한다.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libseccomp2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
