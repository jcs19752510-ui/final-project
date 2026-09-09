import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, coding, interview, media, recruiter, report
from app.config import settings
from app.core.errors import AppError
from app.services.scheduler import create_scheduler

# 2026-09-08 발견(재발방지): 이 프로젝트의 모든 앱 로거(`aimock.*` — stt,
# llm, report, interview, emotion, prosody)가 지금까지 `logger.info(...)`를
# 호출해왔지만, 어디에도 로깅 레벨/핸들러가 설정되어 있지 않아 실제로는
# 한 번도 출력된 적이 없었다(리포트 생성 소요시간 로그를 방금 추가하고
# Docker 컨테이너에서 직접 확인하다가 발견 — `logger.warning(...)`만
# 보이고 `logger.info(...)`는 전혀 안 보임). 원인은 두 가지가 겹쳐 있었다:
# (1) 레벨 미설정 → 기본 WARNING이라 INFO가 걸러짐, (2) 레벨을 낮춰도
# **루트 로거에 핸들러 자체가 없어서**(uvicorn은 `uvicorn`/`uvicorn.access`
# 등 자기 이름의 로거에만 핸들러를 붙이지 루트에는 안 붙임 — 직접
# `logging.getLogger().handlers`로 빈 리스트임을 확인) 어차피 어디로도
# 출력되지 않았음(WARNING 이상만 파이썬 내장 `logging.lastResort`
# 폴백으로 stderr에 찍혀서 우연히 보였던 것). 그래서 "aimock" 로거에
# 레벨과 핸들러를 **직접** 붙인다 — 루트 로거는 건드리지 않아 서드파티
# 라이브러리(SQLAlchemy/httpx/groq 등)의 로그 양은 그대로 유지된다.
_aimock_logger = logging.getLogger("aimock")
_aimock_logger.setLevel(logging.INFO)
if not _aimock_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    _aimock_logger.addHandler(_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="aimock API", lifespan=lifespan)

# 프론트엔드(Vite dev 서버, 기본 5173)에서 크로스오리진 호출 허용.
# 로컬 개발용 origin은 항상 허용 + 2026-09-08(외부 배포 준비) FRONTEND_ORIGINS
# 환경변수로 배포된 프론트엔드 origin(Vercel/Render 등)을 추가로 허용한다.
_dev_origins = [
    "http://localhost:5173",  # Vite dev 서버
    "http://127.0.0.1:5173",
    "http://localhost:8080",  # nginx 프로덕션 빌드 서빙(docker-compose "frontend" 서비스)
    "http://127.0.0.1:8080",
]
_prod_origins = (
    [o.strip() for o in settings.frontend_origins.split(",") if o.strip()]
    if settings.frontend_origins
    else []
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins + _prod_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


# 2026-09-09(보안 강화, F-10 — 전수검사결과_20260909101218.md §F-10): 업로드
# 파일 1개당 크기 상한(media_service.MAX_UPLOAD_FILE_BYTES, 25MB)과는 별개로,
# 요청 자체가 선언한 Content-Length가 지나치게 크면 멀티파트 파싱조차
# 시작하지 않고 그 자리에서 거절한다 — 개별 파일 검증(본문을 다 읽은 뒤에야
# 걸러짐)보다 앞단에서 한 번 더 막는 방어. 표준적인 관행(nginx
# client_max_body_size 등)과 동일한 원리를 애플리케이션 레벨에서도 적용.
_MAX_REQUEST_BODY_BYTES = 30 * 1024 * 1024  # 개별 파일 상한(25MB)보다 여유 있게


@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = None
        if declared_size is not None and declared_size > _MAX_REQUEST_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": (
                            f"요청 본문이 너무 큽니다({declared_size:,} bytes). "
                            f"최대 {_MAX_REQUEST_BODY_BYTES:,} bytes까지 허용됩니다."
                        ),
                    }
                },
            )
    return await call_next(request)


app.include_router(auth.router)
app.include_router(media.router)
app.include_router(interview.router)
app.include_router(coding.router)
app.include_router(report.router)
app.include_router(recruiter.router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
