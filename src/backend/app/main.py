from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, coding, interview, media, recruiter, report
from app.config import settings
from app.core.errors import AppError
from app.services.scheduler import create_scheduler


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


app.include_router(auth.router)
app.include_router(media.router)
app.include_router(interview.router)
app.include_router(coding.router)
app.include_router(report.router)
app.include_router(recruiter.router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
