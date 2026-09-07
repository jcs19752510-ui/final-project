# A0 인수인계 문서 — 웹 AI 모의면접 플랫폼 (aimock)

> `harness/harness_03_handoff_template.md` 형식. 세션이 바뀌어도 여기부터
> 다시 읽으면 전체 맥락이 이어지도록, 단위 완료 시마다(그리고 Phase 경계
> 마다) 갱신합니다.

## 문서 정보
- 프로젝트: 웹 AI 모의면접 플랫폼 (프로젝트 코드: `aimock`)
- 최종 갱신일: 2026-09-07
- 갱신자: AI 작성 → U1/U1-b/U2-a/U3-a는 **실제 실행으로 자기검증 완료**
  (아래 §2), 나머지는 사람 검증 대기 중

## §1. 전체 진행 현황

| 단위 | 상태 | 비고 |
|---|---|---|
| Phase A (기반 구축) | **완료** | ADR 6건, 마스터 TRD, 릴리스계획, 기술컨벤션 작성 완료. 하네스 원문 재검증 갭도 수정 완료, 미결 정책 2건도 사용자 확정 완료 |
| U1 인증/계정+탈퇴 | **완료 — AC 7/7 pass** | 실제 Postgres+Docker로 검증(§2) |
| U1-b 미디어 저장+삭제 | **완료 — AC 5/5 pass** | 실제 Postgres+Docker로 검증(§2) |
| U2-a 턴기반 질문-답변 | **완료 — AC 8/8 pass** | Fake LLM/STT + 실제 Docker HTTP로 검증(§2) |
| U3-a STT+LLM 파이프라인 | **완료 — AC 4/4 pass** | 실제 faster-whisper가 Docker 컨테이너 안에서 실제 오디오로 동작 확인. Gemini는 키 미확보로 실호출 보류 |
| U2-b 라이브 코딩 | 미착수 | |
| U2-c 화이트보드(Could) | 미착수 | |
| U3-b 표정/음성분석 | 미착수 | |
| U4 피드백 리포트 | 미착수 | |
| U5 채용담당자 대시보드 | 미착수 | |

## §2. 이번 세션에서 완료된 것 [AI 초안 → 사람 검증]

- 이 저장소(원래 도메인 중립 하네스 골격)를 사용자 승인으로 프로젝트
  저장소로 전환 (`CLAUDE.md` "저장소 전환 결정" 참조).
- 원본 기획서(PDF 2건, 엔터프라이즈 스펙)를 1인/4주/무예산 제약에 맞게
  재조정하는 ADR 5건 작성(`docs/adr/adr-001`~`005`).
- 마스터 TRD(`docs/trd/aimock_master_trd.md`), 릴리스 계획
  (`docs/release/release_plan.md`), 전역 기술 컨벤션
  (`docs/tech_conventions.md`) 작성.
- **하네스 원문 재검증(2026-09-07, 사용자 요청으로 진행)**: `harness_00_overview.md`
  §5 파일명 규칙 위반(마스터 TRD가 프로젝트코드 없이 `00_master_trd.md`로
  존재) 및 `harness_05_execution_infra.md`의 "기준 브랜치 선언·CI 브랜치
  일치" 요구 위반(CI가 `main` 기준이었으나 실제 기준 브랜치는 `PROD_SCH`)을
  발견 → 모두 수정 완료:
  - `docs/trd/00_master_trd.md` → `docs/trd/aimock_master_trd.md`로 리네임,
    모든 참조 파일 갱신
  - `CLAUDE.md`에 기준 브랜치 `PROD_SCH` 명시적 선언 추가
  - `.github/workflows/ci.yml`의 `branches: [main]` → `[PROD_SCH]` 수정,
    `dependency-scan`/`lint`/`test` 잡을 확정된 스택(Python/FastAPI,
    TS/React, pgvector) 기준으로 실제 내용 채움
  - 프로젝트 코드 `aimock` 확정 및 향후 파일명 규칙을
    `docs/tech_conventions.md`에 명시

- **미결 정책 2건 최종 확정(2026-09-07, 같은 날 후속)**: 원본 미디어는
  "지원자 삭제 요청 전까지 암호화 보관"(ADR-004 갱신), 계정 탈퇴는
  "소프트삭제+30일 유예 후 자동파기"(ADR-006 신규)로 사용자가 직접 선택.
  ADR-003 ERD에 `MEDIA_ASSETS`, `USERS.deleted_at/purge_at` 반영, 마스터
  TRD §3/§5/§7과 릴리스 계획에 U1-b 단위·AC-M6/M7 추가.

- **Phase B — U1/U1-b 구현 완료(2026-09-07)**: `docs/trd/aimock_u1_trd.md`,
  `docs/trd/aimock_u1b_trd.md`, `docs/workorder/aimock_u1_workorder.md`
  작성 후 `src/backend/`에 FastAPI 백엔드 스켈레톤 전체 구현:
  - SQLAlchemy 모델 8종(ADR-003 ERD 전체) + Alembic 초기 마이그레이션
    (`alembic revision --autogenerate` + 수동 검토로 pgvector 확장
    생성문 보강) — 실제 Postgres(Docker, `pgvector/pgvector:pg16`)에
    `alembic upgrade head`로 적용 확인.
  - U1: signup/login/me/withdraw API, JWT, 탈퇴 유예기간 내 자동복구,
    `purge_expired_users` 스케줄러(APScheduler).
  - U1-b: 미디어 업로드(Fernet 암호화)/삭제 API, `purge_user_media`
    연쇄삭제.
  - `docker-compose.yml`(Postgres+App) 작성, 이미지 빌드 확인, 컨테이너로
    기동 후 curl로 signup→login→me→withdraw→me(401) 전체 흐름 실제 호출
    확인(수동 스모크 테스트, 아래 AC 표와 별개로 인프라 자체 동작 검증).

- **AC 대비 결과 (실제 pytest 실행, 목/스텁 없이 실제 Postgres 컨테이너
  대상)**:

  | 단위 | AC | 결과 |
  |---|---|---|
  | U1 | AC-1~AC-7 (7개) | **전부 PASS** |
  | U1-b | AC-1~AC-5 (5개) | **전부 PASS** |

  실행 로그 요약: `pytest tests/backend -v` → `12 passed`. `ruff check
  src/backend` → 이슈 없음. `mypy src/backend/app` → 이슈 없음.

- **판단 근거(스펙에 없어 AI가 채운 세부사항)**:
  - JWT 페이로드는 `sub`(user id)+`exp`만 사용(역할 등 추가 클레임 없음) —
    권한 체크는 매 요청마다 DB에서 최신 상태를 다시 읽어 처리(탈퇴 즉시
    반영 요건, TRD AC-5 때문에 캐시성 클레임을 신뢰하지 않기로 함).
  - 미디어 삭제 API는 소프트 삭제 없이 즉시 하드 삭제(ADR-004에 "원본
    미디어는 삭제 즉시 영구 삭제" 명시와 일치).

- **Phase B — U2-a/U3-a 구현 완료(2026-09-07, 같은 날 계속)**:
  `docs/trd/aimock_u2a_trd.md`, `aimock_u3a_trd.md`,
  `docs/workorder/aimock_u2a_workorder.md` 작성 후 구현:
  - `LLMProvider`(Gemini 실제 구현, `google-genai` SDK) /
    `STTProvider`(faster-whisper 실제 구현) 어댑터 패턴 + 테스트용
    `FakeLLMProvider`/`FakeSTTProvider`(`app.dependency_overrides`로 교체).
  - 면접 시작/턴 제출/종료 API, 질문은행 시드 10문항 +
    category/difficulty 필터 기반 RAG(임베딩 검색은 API 키 확보 전까지
    보류 — TRD §7 미결).
  - **실제 faster-whisper `tiny` 모델을 다운로드해 로드하고, 실제 오디오
    바이트(WAV)로 `FasterWhisperProvider.transcribe()` 동작을 수동
    검증**(의미있는 음성 인식 정확도는 실제 사람 음성 필요 — 범위 밖).
  - Gemini는 `GEMINI_API_KEY` 미확보로 실제 호출은 하지 않음, SDK
    시그니처는 실제 라이브러리를 설치·검사해 정확하게 작성.

- **AC 대비 결과(U2-a/U3-a, 실제 pytest 실행)**:

  | 단위 | AC | 결과 |
  |---|---|---|
  | U2-a | AC-1~AC-7 (7개) | **전부 PASS** |
  | U3-a | AC-1,3,4 (자동화 3개) | **전부 PASS** |
  | U3-a | AC-2(실제 STT 동작) | **PASS (수동 확인, 자동화 대상 아님)** |

  실행 로그: `pytest tests/backend -v` → `21 passed`(U1+U1-b+U2-a+U3-a
  전체 누적). `ruff`/`mypy` 클린. 상세는
  `내부테스트결과서/U2a_U3a_턴기반질문답변STT_LLM파이프라인테스트_20260907211637.md`.

- **판단 근거 추가**:
  - `Transcript.created_at`을 DB `server_default now()`에서 Python
    `datetime.now(timezone.utc)` 기본값으로 변경 — 같은 트랜잭션 내 여러
    INSERT가 server_default를 쓰면 전부 동일 타임스탬프가 되어 대화
    순서가 뒤섞이는 문제를 실제 테스트 중 발견하고 수정(§3에도 기록).
  - `retrieve_candidates()`는 벡터 검색이 아닌 category/difficulty
    필터로 구현(ADR-002 미결 항목 기본값 적용, API 키 확보 후 재검토).

## §3. 발견된 편차 (TRD/가정과 실제가 다름) [필수 기록]

| 무엇을 가정했는가 | 실제로는 어땠는가 | 어떻게 처리했는가 |
|---|---|---|
| 이 저장소는 도메인 중립 하네스 골격만 유지한다(CLAUDE.md 원안) | 사용자가 이 저장소 자체를 실제 프로젝트로 쓰길 원함 | 사용자 확인(AskUserQuestion) 후 CLAUDE.md/README.md를 전환 내용으로 갱신 |
| 하네스 SOP는 `harness_00_definition.md`의 요약만 참고해도 충분할 것 | 실제로는 `harness_00_overview.md`(원문 SOP)에 파일명 규칙 등 더 구체적인 강제 규칙이 있었고, 요약본만 보고 진행해 파일명 규칙을 놓침 | 원문 5종(`00_overview`, `02`, `03`, `05`, `10`)을 전부 다시 읽고 이 A0 문서 §2에 수정 내역 기록 |
| CI의 기준 브랜치가 `main`일 것 | 이 저장소의 실제 기준 브랜치는 `PROD_SCH` | `CLAUDE.md`에 명시 선언 + `ci.yml` 수정 |
| `docs/tech_conventions.md`에 적어둔 "bcrypt"로 비밀번호 해시가 문제없이 될 것 | `passlib==1.7.4`가 최신 `bcrypt`(5.x)와 호환성 버그(72바이트 자가진단 예외, `__about__` 속성 없음)로 실제 실행 시 500 에러 발생 | `passlib` 제거, `bcrypt` 라이브러리를 직접 사용하도록 `app/core/security.py` 변경 + `requirements.txt`에 `bcrypt==4.2.1` 고정 |
| pydantic `EmailStr`가 기본 설치로 동작할 것 | 로컬 아나콘다 환경엔 `email-validator`가 이미 있어 통과했지만, 신규 Docker 이미지(`pip install -r requirements.txt`만)에서는 `ImportError` 발생 | `requirements.txt`를 `pydantic[email]`로 수정, 이미지 재빌드로 재현 확인 |
| 로컬 Postgres 기본 포트(5432)를 그대로 쓸 수 있을 것 | 이 머신에 이미 무관한 다른 프로젝트의 Postgres 컨테이너가 5432를 점유 중 | `docker-compose.yml`을 호스트 포트 `55432`로 변경(컨테이너 내부는 여전히 5432), `.env.example`에 이유 명시 |
| pytest-asyncio 기본 설정으로 SQLAlchemy 비동기 엔진을 여러 테스트에서 재사용해도 될 것 | 테스트마다 새 이벤트 루프가 생성되어 "Task ... attached to a different loop" 에러 발생 | `pytest.ini`에 `asyncio_default_fixture_loop_scope`/`asyncio_default_test_loop_scope = session` 추가 |
| `transcripts.created_at`을 DB `server_default now()`로 두면 대화 순서 정렬에 문제없을 것 | 한 트랜잭션 안에서 여러 행을 INSERT하면 Postgres `now()`가 트랜잭션 시작 시각으로 고정되어 전부 같은 값이 됨 → `ORDER BY created_at`이 무의미해짐 | `Transcript.created_at`을 Python 쪽 `datetime.now(timezone.utc)` 기본값으로 변경(모델 레벨, 마이그레이션 불필요) |
| `requirements.txt`에 개별 패키지를 최신 안정 버전으로 고정해두면 `pip install -r requirements.txt`가 항상 될 것 | `pydantic==2.10.4`가 나중에 추가한 `google-genai==2.22.0`의 요구 버전(`>=2.12.5`)과 충돌 — 로컬 환경엔 이미 더 새 버전이 깔려 있어 개별 설치로는 안 걸렸고, Docker로 처음부터 새로 설치할 때만 드러남 | `pydantic`을 `2.13.4`로 상향, 이후 새 의존성 추가 시마다 Docker 이미지 재빌드로 재확인하는 습관 필요 |
| Git Bash에서 `curl -F file=@경로`에 `/c/Users/...`(MSYS 경로)를 써도 될 것 | 이 환경의 `curl`이 mingw64 네이티브 빌드라 MSYS 경로를 못 읽고 `curl: (26)` 오류 발생(애플리케이션 버그 아님, 테스트 스크립트 문제) | `C:/Users/...` 형식(네이티브 Windows, 슬래시)으로 바꿔서 해결 — 이 환경에서 향후 curl 파일 업로드 테스트 시 항상 이 형식 사용 |

## §4. 남은 것 / 다음 세션에서 할 일
- [ ] 마스터 TRD §2(기능요구사항)/§3(비기능요구사항) 표 내용을 사람이 직접
  라인 단위로 검토·승인 (지금까지는 AI 초안 + 상위 방향 승인만 있었음)
- [x] §6의 미결 정책 2건 확정 — 2026-09-07: 원본 미디어는 지원자 삭제
  요청 전까지 암호화 보관(ADR-004), 계정 탈퇴는 소프트삭제+30일 유예
  자동파기(ADR-006)
- [x] U1(인증/계정+탈퇴) + U1-b(미디어 저장+삭제) 구현 및 AC 12/12 검증
  완료 (2026-09-07)
- [x] U2-a(턴 기반 질문-답변) + U3-a(STT/LLM 파이프라인) 구현 및 AC 11/11
  검증 완료(자동화 10 + 수동 1) (2026-09-07)
- **사람의 diff 리뷰는 U1/U1-b/U2-a/U3-a 전부 아직 없음**
  (harness_00_overview §4 규칙 3 "리뷰 필수"). git 커밋/브랜치/PR은
  CLAUDE.md 금지 규칙에 따라 AI가 하지 않음 — 사용자가 직접 커밋해야 함.
- [ ] **다음 단위: U2-b(라이브 코딩) 또는 U4(피드백 리포트)** — 릴리스
  계획 순서상 Week3 진입. `GEMINI_API_KEY`를 아직 확보하지 못했다면,
  실제 LLM 응답 품질(꼬리질문 자연스러움 등)은 계속 Fake로만 검증되고
  있다는 점을 다음 세션 시작 시 재확인할 것.

- [x] **미검증 항목 소급 테스트 완료(2026-09-07, 사용자 지시)**: 이전에
  "이번엔 안 함"으로 남겨뒀던 Docker `app` 이미지 재빌드(새 의존성
  포함) + 실제 HTTP 전체 흐름 호출 + Alembic 다운그레이드(롤백)를 모두
  실행. 그 과정에서 실제 버그 2건을 발견해 고쳤다:
  1. `requirements.txt`의 `pydantic==2.10.4`가 새로 추가한
     `google-genai==2.22.0`의 요구사항(`pydantic>=2.12.5`)과 충돌해
     **Docker 이미지 빌드 자체가 실패**(로컬 아나콘다 환경엔 이미 더
     새 버전이 깔려 있어서 지금까지 못 보고 지나감) → `2.13.4`로 수정.
  2. `GEMINI_API_KEY` 없이 턴 제출 시 **500**이 나던 것을 발견 →
     `ServiceUnavailableError`(503) 신설해 정리, TRD에 AC-8로 추가.
  Alembic `downgrade -1`/`upgrade head` 라운드트립도 실제 Postgres에서
  검증(10개 테이블 삭제→복구 확인) — 이 경로는 이전에 한 번도
  실행해본 적이 없었음. 상세는
  `내부테스트결과서/Docker전체스택실HTTP및마이그레이션롤백테스트_20260907213116.md`.

## §5. 다음 세션 착수 전 반드시 확인할 것
- 사람이 `src/backend/` diff를 리뷰했는지, 그리고 로컬에서 커밋/브랜치를
  만들었는지 먼저 확인할 것(AI는 git 명령을 실행하지 않았으므로 현재
  워킹트리에 파일만 존재하고 커밋되지 않은 상태).
- 로컬 개발 환경 기동 방법: `docker compose up -d`(Postgres+App) 또는
  `cd src/backend && python -m alembic upgrade head` 후
  `uvicorn app.main:app --reload`. `.env`는 `.env.example` 참고해 직접
  생성(커밋 금지).
- 테스트 실행: `pytest tests/backend -v` (사전에 Postgres 컨테이너 기동
  및 `alembic upgrade head` 필요, `docker compose up -d postgres`로 가능).
- `harness_00_overview.md` §6 품질 게이트 체크리스트를 매 단위 완료 시
  실제로 확인했는지.

## §6. 리스크/미결 정책 (아직 사람의 최종 결정이 안 난 것)

| 항목 | 상태 |
|---|---|
| 원본 오디오/비디오 영구 저장 여부 (ADR-004) | **확정** — 지원자 삭제 요청 전까지 암호화 보관 |
| 계정 탈퇴 시 데이터 처리 (ADR-006) | **확정** — 소프트삭제 + 30일 유예 후 스케줄러 자동 물리삭제 |
| 30일 유예기간 값의 법무적 타당성 | 미확정(AI 제안 기본값) — MVP 범위에서는 그대로 진행, 실서비스 전환 시 재검토 필요 |
| Gemini 무료 티어 쿼터 소진 시 대응(Groq 전환) | 방향은 확정(ADR-002), 구현 전 최종 확인 필요 |
