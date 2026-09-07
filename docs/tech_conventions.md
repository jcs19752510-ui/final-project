# 전역 기술 컨벤션 — 웹 AI 모의면접 플랫폼 (MVP)

> `harness/harness_13_tech_conventions.md`의 취지(전역 표준을 프로젝트
> 착수 시 한 번만 고정)를 1인 프로젝트 규모에 맞게 간소화해 적용합니다.
> 4주간 여러 세션에 걸쳐 코드를 작성하므로, 세션이 바뀌어도 동일한 규약을
> 따르기 위한 최소 기준입니다.

## 하네스 문서 파일명 규칙 (`harness_00_overview.md` §5 준수)

- **프로젝트 코드: `aimock`** (2026-09-07 확정 — "AI mock interview". 영문/
  숫자만 사용하는 하네스 규칙 때문에 한글 프로젝트명 대신 이 코드를 씀)
- 형식: `aimock_{단위코드}_{문서유형}.md` — 단위코드는
  `docs/release/release_plan.md` §1의 단위 코드를 소문자·하이픈제거로
  사용(`U2-a` → `u2a`), 문서유형은 `trd`/`workorder`/`handoff`/`prompt`.
- 예: `docs/trd/aimock_u1_trd.md`, `docs/workorder/aimock_u1_workorder.md`
- 마스터 TRD/A0 인수인계처럼 "단위 코드"가 없는 전체 단위 문서는 `master`/
  `a0`를 단위코드 자리에 사용: `aimock_master_trd.md`, `aimock_a0_handoff.md`
- **예외(사용자 지시로 유지)**: `자동진행/` 폴더 파일명은 사용자가 명시적
  으로 "업무핵심주제+yyyymmddHHMMss.md"(한글 포함) 형식을 지정했으므로
  이 규칙의 적용 대상에서 제외한다. ADR(`docs/adr/adr-NNN-*.md`)과 릴리스
  계획(`docs/release/release_plan.md`)도 harness_00 §5의 문서유형 약어
  목록(trd/workorder/handoff/prompt)에 포함되지 않는 별도 문서라 이 패턴을
  강제하지 않는다(다만 영문 파일명 원칙 자체는 지킴).

## 언어/프레임워크
- 백엔드: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy(async) + Alembic
- 프론트엔드: React + Vite + TypeScript (Next.js는 SSR/라우팅 오버헤드가
  이번 규모에 불필요하다고 판단해 제외 — 필요 시 재검토)
- DB: PostgreSQL 16 + pgvector 확장 (ADR-003)

## API 규약
- REST, 경로 접두사 `/api/v1/`
- 요청/응답 바디는 항상 JSON, 필드명은 `snake_case`
- 에러 응답 포맷 고정:
  ```json
  { "error": { "code": "STRING_CODE", "message": "사용자용 메시지" } }
  ```
- 인증: JWT Bearer 토큰(`Authorization: Bearer {token}`), 세션 상태는
  서버 메모리/Redis가 아닌 **DB(users/sessions 불필요, JWT 자체가 상태 보유
  — 단, 로그아웃/폐기는 만료시간으로만 처리, 블랙리스트는 MVP 범위 밖)**

## 네이밍
- DB 테이블/컬럼: `snake_case`, 복수형 테이블명(`users`, `interviews`)
- Python 변수/함수: `snake_case`, 클래스: `PascalCase`
- TypeScript/React: 컴포넌트 `PascalCase`, 변수/함수 `camelCase`
- 코드 주석/커밋 메시지: 한국어 허용(1인 프로젝트 문서와 통일)

## 폴더 구조 (`src/`)
```
src/
  backend/
    app/
      api/            # FastAPI 라우터
      services/        # 비즈니스 로직 (BackgroundTasks에서 재사용 가능하게 분리)
      models/          # SQLAlchemy 모델
      schemas/         # Pydantic 스키마
      ai/              # LLM/STT/감정분석 어댑터
    alembic/
  frontend/
    src/
      pages/
      components/
      api/             # 백엔드 API 클라이언트
```

## LLM 클라이언트 어댑터 규약 (ADR-002 관련)
- `src/backend/app/ai/llm_provider.py`에 `LLMProvider` 인터페이스(추상
  클래스)를 정의하고, `GeminiProvider`가 이를 구현. 향후 Groq/Ollama로
  교체 시 이 인터페이스만 구현하면 되도록 유지 — **다른 코드에서 Gemini
  SDK를 직접 import하지 않는다.**
- LLM 응답은 항상 구조화된 JSON(Pydantic 모델로 검증)으로 받는다 —
  원본 기획서 §5.1.2의 Structured Output 원칙 유지.

## 환경변수
- `.env`(커밋 금지, `.gitignore`에 이미 포함되어 있는지 세션 시작 시 확인)
- 필수 키: `DATABASE_URL`, `GEMINI_API_KEY`, `JWT_SECRET`
- 샘플은 `.env.example`로 관리(실제 키 값 없이 키 이름만)

## 테스트
- 백엔드: `pytest`, 서비스 로직 단위테스트 우선 (AI 응답은 목/스텁으로 대체)
- AC(인수조건) 1개당 최소 1개 이상의 테스트 케이스 매핑을 원칙으로 함
  (`harness_01` §6 테스트 시나리오 표 참조)

## 갱신 시점
- 새로운 외부 라이브러리를 도입할 때(특히 ADR 대상 여부 확인)
- 명명 규칙 위반이 반복적으로 발견될 때
