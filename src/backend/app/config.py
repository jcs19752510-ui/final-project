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
    stt_model_size: str = "tiny"
    turn_max_answer_chars: int = 800  # aimock_u2a_trd.md §3 (F-003 대체)
    # 2026-09-08(외부 배포 준비): 배포된 프론트엔드 origin(예: Vercel/Render
    # 정적 사이트 URL)을 CORS 허용 목록에 추가하기 위함. 쉼표로 여러 개
    # 지정 가능(예: "https://foo.vercel.app,https://bar.onrender.com").
    # 로컬 개발용 origin은 app/main.py에 이미 하드코딩돼 있어 이 값은
    # 비워둬도(None) 로컬 개발에 영향 없음.
    frontend_origins: str | None = None


settings = Settings()
