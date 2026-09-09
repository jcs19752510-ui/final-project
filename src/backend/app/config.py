from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aimock"
    # 2026-09-08(외부 배포 준비): Neon 등 관리형 Postgres는 SSL을 요구하는데,
    # asyncpg는 DATABASE_URL 쿼리스트링의 libpq식 `sslmode`/`channel_binding`을
    # 인식하지 못해 그대로 URL에 붙이면 연결 자체가 실패한다(SQLAlchemy
    # asyncpg 드라이버의 알려진 제약). 그래서 URL엔 SSL 파라미터를 넣지 않고,
    # 이 플래그로 `connect_args={"ssl": "require"}`를 코드에서 명시적으로
    # 전달한다 — 로컬 Docker Postgres는 SSL을 안 쓰므로 기본값 False 유지.
    db_ssl_require: bool = False
    jwt_secret: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    # 실제 값은 .env(MEDIA_ENCRYPTION_KEY)로 주입 — 여기 하드코딩하지 않음.
    # 로컬 최초 셋업: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    media_encryption_key: str | None = None
    media_storage_dir: str = "uploads"
    account_deletion_grace_days: int = 30
    gemini_api_key: str | None = None  # ADR-002 — https://aistudio.google.com 무료 키
    groq_api_key: str | None = None  # ADR-002 — https://console.groq.com 무료 키(2026-09-08, Gemini 무료 티어 일일 한도 소진 대응으로 전환)
    stt_model_size: str = "tiny"  # FasterWhisperProvider(로컬, 현재 미사용)용 — ADR-008 참조
    groq_stt_model: str = "whisper-large-v3-turbo"  # ADR-008 — GroqWhisperProvider(현재 실사용)용
    turn_max_answer_chars: int = 800  # aimock_u2a_trd.md §3 (F-003 대체)
    # ADR-008 연계(2026-09-08): 면접 질문 개수를 LLM 판단에만 맡기면 안 끝나는
    # 문제(운영 환경 실사용 중 턴 25까지 진행되는 것을 실제로 확인)가 있어
    # 서버가 최소/최대를 강제한다. aimock_u2a_trd.md §3 참조.
    interview_min_questions: int = 5
    interview_max_questions: int = 10
    # 2026-09-08(외부 배포 준비): 배포된 프론트엔드 origin(예: Vercel/Render
    # 정적 사이트 URL)을 CORS 허용 목록에 추가하기 위함. 쉼표로 여러 개
    # 지정 가능(예: "https://foo.vercel.app,https://bar.onrender.com").
    # 로컬 개발용 origin은 app/main.py에 이미 하드코딩돼 있어 이 값은
    # 비워둬도(None) 로컬 개발에 영향 없음.
    frontend_origins: str | None = None


settings = Settings()

# 2026-09-09(보안 강화, F-1 — 99.모의면접_전수검사/전수검사결과_20260909101218.md):
# jwt_secret이 기본값(공개된 문자열) 그대로면 앱을 아예 못 뜨게 막는다
# (fail-fast). JWT는 모든 인증 요청마다 쓰이는 서명 키라, 이걸
# media_encryption_key(app/core/crypto.py)처럼 "실제 쓰일 때"에야 늦게
# 걸러지게 두면 앱이 겉보기엔 정상 기동한 것처럼 보여 위험이 배포/모니터링
# 단계에서 가려질 수 있다 — 그래서 기동 시점(모듈 임포트 시점)에 즉시
# 막는다. 로컬 docker-compose(.env)와 Render 운영 환경은 이미 실제 랜덤
# 값을 넣어둔 상태라 영향 없고, pytest(conftest.py)도 별도 시크릿
# ("test-only-secret")을 명시적으로 쓰고 있어 영향 없음 — 오직 "아무 값도
# 안 넣은 상태"만 걸러낸다.
_INSECURE_DEFAULT_JWT_SECRET = "dev-only-secret-change-me"
if settings.jwt_secret == _INSECURE_DEFAULT_JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET 환경변수가 설정되지 않아 공개된 기본값이 그대로 쓰이고 "
        "있습니다 — 보안상 이 상태로는 서버를 시작할 수 없습니다. "
        "python -c \"import secrets; print(secrets.token_urlsafe(48))\" 로 "
        "충분히 긴 무작위 값을 생성해 JWT_SECRET 환경변수(.env 또는 배포 "
        "환경변수)에 넣으세요."
    )
