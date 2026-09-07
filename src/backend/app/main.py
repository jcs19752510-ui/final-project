from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, coding, interview, media, recruiter, report
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
# MVP 로컬 데모 목적이라 개발용 origin만 허용(운영 배포 시 재검토 필요).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev 서버
        "http://127.0.0.1:5173",
        "http://localhost:8080",  # nginx 프로덕션 빌드 서빙(docker-compose "frontend" 서비스)
        "http://127.0.0.1:8080",
    ],
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
