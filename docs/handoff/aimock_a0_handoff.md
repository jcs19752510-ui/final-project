# A0 인수인계 문서 — 웹 AI 모의면접 플랫폼 (aimock)

> `harness/harness_03_handoff_template.md` 형식. 세션이 바뀌어도 여기부터
> 다시 읽으면 전체 맥락이 이어지도록, 단위 완료 시마다(그리고 Phase 경계
> 마다) 갱신합니다.

## 문서 정보
- 프로젝트: 웹 AI 모의면접 플랫폼 (프로젝트 코드: `aimock`)
- 최종 갱신일: 2026-09-08
- 갱신자: AI 작성 → U1/U1-b/U2-a/U3-a/프론트엔드/프로덕션 강화 8건은
  **실제 실행으로 자기검증 완료** (아래 §2), 나머지는 사람 검증 대기 중

## §1. 전체 진행 현황

| 단위 | 상태 | 비고 |
|---|---|---|
| Phase A (기반 구축) | **완료** | ADR 6건, 마스터 TRD, 릴리스계획, 기술컨벤션 작성 완료. 하네스 원문 재검증 갭도 수정 완료, 미결 정책 2건도 사용자 확정 완료 |
| U1 인증/계정+탈퇴 | **완료 — AC 7/7 pass** | 실제 Postgres+Docker로 검증(§2) |
| U1-b 미디어 저장+삭제 | **완료 — AC 5/5 pass** | 실제 Postgres+Docker로 검증(§2) |
| U2-a 턴기반 질문-답변 | **완료 — AC 8/8 pass** | Fake LLM/STT + 실제 Docker HTTP로 검증(§2) |
| U3-a STT+LLM 파이프라인 | **완료 — AC 4/4 pass** | 실제 faster-whisper가 Docker 컨테이너 안에서 실제 오디오로 동작 확인. Gemini는 키 미확보로 실호출 보류 |
| U2-b 라이브 코딩 | **완료 — AC 7/7 pass** | 실제 subprocess + Docker HTTP 검증(§2). ⚠️ ADR-007 보안 한계 필독 |
| U2-c 화이트보드(Could) | 미착수 | 사람이 여유 시간 확보 시 진행 |
| U3-b 표정/음성분석 | **완료(엔진+UI) — AC 5/5 pass** | 사용자 제공 실제 얼굴영상/음성으로 검증(§2). 실시간 웹캠 캡처 UI까지 구현·검증 완료 |
| U4 피드백 리포트 | **완료 — AC 8/8 pass** | Fake Generator + 실제 Docker HTTP로 검증(§2) |
| U5 채용담당자 대시보드 | **완료 — AC 6/6 pass** | 실제 Docker HTTP로 검증(§2) |
| 프론트엔드(React, U1/U2-a/U2-b/U4/U5 화면) | **완료 — AC-F 9/10 pass** | 실제 브라우저+Docker로 검증(§2). AC-F6은 `GEMINI_API_KEY` 미확보로 부분 검증 |
| 프로덕션 강화 8건(테스트/CI/nginx/레이트리밋/세션만료/샌드박스강화/취약점패치/TRD검토) | **완료** | §2 참조, 검토 중 원본 오디오 미보관 버그(ADR-004 미이행)와 AC-M6 UI 부재도 함께 발견·수정 |

> **🎯 마일스톤: 마스터 TRD의 Must-have 단위(U1/U1-b/U2-a/U3-a/U2-b/U4/U5)
> 전부 구현·검증 완료 (2026-09-07).** 누적 pytest 43/43 pass. 남은 것은
> Could-have(U2-c)와 사람이 자료를 줘야 진행 가능한 U3-b, 그리고 전체에
> 대한 사람의 diff 리뷰 + git 커밋.

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

- **Phase B — U2-b(라이브 코딩) 구현 완료(2026-09-07, 사용자가 이번
  세션 자동진행을 명시적으로 승인한 후 계속)**:
  `docs/trd/aimock_u2b_trd.md`, `docs/workorder/aimock_u2b_workorder.md`,
  **`docs/adr/adr-007-code-execution-sandbox.md`**(신규 — 코드 실행
  샌드박스 방식, ⚠️ 보안 한계 명시) 작성 후 구현: `CodeExecutor` 어댑터
  + `SubprocessExecutor`(타임아웃 5초, 자식 프로세스 환경변수를
  PATH/SYSTEMROOT 등 최소 allowlist로 제한해 앱 시크릿 유출 방지),
  코드 제출 API. **자동진행으로 결정한 것**(근거:
  `자동진행/U2b샌드박스및작업범위자동결정_20260907213841.md`): (1) 보안
  아키텍처 결정(ADR-007)을 사람 승인 없이 진행, (2) F-004 원안의 "AI
  코드 평가"를 U2-b 범위에서 빼고 U4로 이동.

- **AC 대비 결과(U2-b, 실제 subprocess 실행 + 실제 Docker HTTP 호출)**:

  | 단위 | AC | 결과 |
  |---|---|---|
  | U2-b | AC-1~AC-7 (7개) | **전부 PASS** |

  실행 로그: `pytest tests/backend -v` → **`29 passed`**(전체 누적).
  실제 컨테이너에서 무한루프 코드가 정확히 5.08초 후 타임아웃되고,
  `os.environ` 유출 시도에도 앱 시크릿이 안 나오는 것을 curl로 직접
  확인. 상세는
  `내부테스트결과서/U2b_라이브코딩샌드박스테스트_20260907214804.md`.

- **Phase B — U4(피드백 리포트) 구현 완료(2026-09-07, 자동진행 계속)**:
  `docs/trd/aimock_u4_trd.md`, `docs/workorder/aimock_u4_workorder.md`
  작성 후 구현: `ReportGenerator` 어댑터(U2-a/U3-a와 동일 패턴, Gemini
  실제 구현 + Fake) + LLM 불필요한 로컬 키워드 추출기(`keyword_extractor.
  extract()`, 형태소 분석기 없이 간이 토큰화). 리포트 생성/조회 API.
  **자동진행 판단**: 표정/음성 타임라인은 U3-b 미착수라 빈 배열로 처리,
  F-004의 "AI 코드 평가"는 U2-b에서 넘겨받아 이번 리포트 생성 시 코드
  제출 이력도 함께 LLM 컨텍스트에 포함시킴.

- **AC 대비 결과(U4, Fake Generator + 실제 Docker HTTP)**:

  | 단위 | AC | 결과 |
  |---|---|---|
  | U4 | AC-1~AC-8 (8개) | **전부 PASS** |

  실행 로그: `pytest tests/backend -v` → **`37 passed`**(전체 누적).
  실제 컨테이너에서 `GEMINI_API_KEY` 없이 리포트 생성 요청 시 503이
  정확히 재현되고, live 상태 생성 시도(409)·미생성 조회(404)도 curl로
  직접 확인. 상세는
  `내부테스트결과서/U4_피드백리포트생성조회테스트_20260907215737.md`.

- **Phase B — U5(채용담당자 대시보드) 구현 완료(2026-09-07, 자동진행
  계속 → Must-have 전체 완료)**: `docs/trd/aimock_u5_trd.md`,
  `docs/workorder/aimock_u5_workorder.md` 작성 후 `require_recruiter`
  인증 의존성 + 목록/리포트열람/통계 API 구현. **판단 근거**: recruiter는
  다른 단위와 반대로 `candidate_id` 소유권 검사를 하지 않음(전체 열람이
  정당한 권한) — TRD §0-1에 이 차이를 명시적으로 기록.

- **AC 대비 결과(U5, 실제 Docker HTTP)**:

  | 단위 | AC | 결과 |
  |---|---|---|
  | U5 | AC-1~AC-6 (6개) | **전부 PASS** |

  실행 로그: `pytest tests/backend -v` → **`43 passed`**(전체 누적,
  U1~U5). `ruff` 클린, `mypy` → 53개 파일 이슈 없음. 실제 컨테이너에서
  candidate가 대시보드 접근 시 403, recruiter는 200으로 전체 목록/통계
  조회됨을 curl로 직접 확인. 상세는
  `내부테스트결과서/U5_채용담당자대시보드테스트_20260907220531.md`.

**🎯 마일스톤: 마스터 TRD의 Must-have 단위 전체(U1/U1-b/U2-a/U3-a/U2-b/
U4/U5) 구현·검증 완료.**

- **프론트엔드(React/Vite) 전체 화면 구현 완료(2026-09-07, 신규 세션에서
  인계받아 자동진행)**: `docs/trd/aimock_frontend_trd.md`(5개 화면 통합
  TRD),  `docs/workorder/aimock_frontend_workorder.md` 작성 후
  `src/frontend/` 전체 구현(로그인/회원가입/탈퇴, 면접장, 라이브 코딩,
  피드백 리포트, 채용담당자 대시보드). 백엔드에 CORS 미들웨어 추가(최소
  배선, 스코프 위반 아님). 판단 근거:
  `자동진행/프론트엔드TRD통합및착수결정_20260907232301.md`.

- **AC 대비 결과(AC-F1~F10, 실제 Docker 백엔드 + Vite dev 서버 + 실제
  브라우저 조작)**:

  | 항목 | AC | 결과 |
  |---|---|---|
  | 프론트엔드 | AC-F1~F5, F7~F10 (9개) | **전부 PASS** |
  | 프론트엔드 | AC-F6(면접 턴 제출→다음 질문 갱신) | **부분 PASS** — multipart 계약은 실증, LLM 응답 갱신은 `GEMINI_API_KEY` 확보 후 재검증 필요 |

  상세는
  `내부테스트결과서/프론트엔드_U1U2aU2bU4U5화면수동테스트_20260907233851.md`.
  테스트 중 실제 버그 1건 발견·수정(§3 표 참조 — `ReportPage.tsx` 409
  처리 오류).

- **프로덕션 강화 8건 완료(2026-09-08, 사용자의 "20년차 재검토" 요청 →
  결과 8개 항목 전부 승인받아 자동진행)**: 프론트 유닛테스트(Vitest 16건),
  CI 프론트 빌드/테스트 단계, nginx 프로덕션 정적 서빙, 로그인 브루트포스
  방어(레이트리밋), JWT 만료 시 자동 로그아웃, ADR-007 샌드박스 리소스
  제한 강화, dompurify 취약점 패치, 마스터 TRD §2/§3 라인 검토. 판단
  근거: `자동진행/20260908_프로덕션강화8건_자동진행결정.md`. 검증 결과:
  `내부테스트결과서/20260908_프로덕션강화8건_검증결과.md`.
- **검토 중 발견해 즉시 수정한 것**: 마스터 TRD 라인 검토 도중, 면접 턴
  제출이 STT 변환에만 오디오를 쓰고 ADR-004(원본 오디오 암호화 보관)가
  요구하는 저장을 실제로는 호출하지 않던 것을 발견 → 연결.
  AC-M6(리포트 화면에서 원본 미디어 삭제)도 API만 있고 프론트 UI가
  아예 없었음 → `GET /api/v1/interviews/{id}/media`(신규) +
  `ReportPage.tsx` "원본 답변 오디오 관리" 섹션으로 구현. 둘 다 실제
  Docker 컨테이너 + 브라우저로 재검증 완료, pytest 4건 추가(전체
  **47/47 pass**).
- **마스터 TRD §2/§3 라인 검토 결과**: F-001(RAG 후보검색 문구가 실제
  구현보다 과장됨), F-002/F-004(이미지 입력·구조화된 코드평가 Must인데
  실제론 부분/미구현), F-006(발화속도 계산 로직 자체가 없음),
  N-004(`key_observations` 필드명이 실제 스키마에 없음) 등 발견 — 문서
  정정 여부는 사람 결정 필요.
  `docs/trd/aimock_master_trd_review_20260908.md` 참조.

- **GEMINI_API_KEY 확보 및 실제 LLM 첫 검증(2026-09-08, 사용자 제공)**:
  코드에 고정돼 있던 `gemini-2.0-flash`가 이미 단종(404)된 것과, 교체한
  `-latest` 별칭도 그 시점 일시 과부하(503)였던 것을 실제 호출로 발견 →
  안정적인 `gemini-2.5-flash-lite`로 최종 고정(`app/ai/llm.py`,
  `app/ai/report.py`). Gemini API 예외를 원시 500이 아닌 표준 503으로
  변환하는 에러 핸들링도 추가. **실제 Gemini로 면접 질문 생성·리포트
  채점 전 과정을 처음으로 검증**(무음 오디오에 대해 AI가 임의로 좋은
  점수를 주지 않고 정확히 낮게 평가하는 것까지 확인 — 핵심 가치 제안
  실증). 상세:
  `내부테스트결과서/GEMINI_API_KEY_실제LLM검증_20260908011143.md`.
- **마스터 TRD §2/§3 사람 승인 및 문서 정정 완료(2026-09-08)**: 검토
  결과를 사용자가 "문서를 실제 구현에 맞게 고치기"로 확정, 마스터 TRD에
  "실제 구현 상태" 열을 추가해 F-001(RAG 미구현)/F-002(Should로 하향)/
  F-003(시간→길이 트리거 정정)/F-004(구조화 평가 없음 명시)/F-006(발화
  속도 삭제)/N-004(key_observations 위치 정정) 반영. 문서 상태를
  "초안"→"확정(v0.2)"으로 갱신.

- **U3-b(표정/음성운율 분석) 엔진 구현 완료(2026-09-08, 사용자가 실제
  얼굴 영상(mp4)/음성(m4a) 샘플 제공)**: `docs/trd/aimock_u3b_trd.md`,
  `docs/workorder/aimock_u3b_workorder.md` 작성 후
  `app/ai/emotion.py`(DeepFace)·`app/ai/prosody.py`(librosa) 어댑터 구현,
  `report_service.generate_report()`에 배선(`video_frame`/`audio` 미디어가
  있으면 분석해 `emotion_timeline`/`voice_prosody`에 반영, 없으면 조용히
  빈 배열). **실제 사용자 샘플로 검증**: 표정 `neutral 95.3%`(얼굴 검출
  신뢰도 96%), 음성 피치 `115.23Hz`(남성 음성대 정상 범위) — 둘 다
  실제 값이 나옴을 확인(가짜/의미없는 결과 아님). pytest 51/51(신규 4건).
  **명시적으로 범위에서 뺀 것**: 프론트엔드에서 면접 중 실시간으로 얼굴을
  캡처해 업로드하는 UI/파이프라인은 별도 작업(TRD §0) — 지금은 "엔진은
  준비됐지만 자동으로 트리거되는 라이브 캡처는 없음" 상태.
  **실제 Docker 컨테이너(배포 환경)에서도 API 전체 흐름(회원가입→면접→
  미디어 업로드→리포트 생성)으로 재검증 완료** — 로컬 스크립트 검증과
  동일한 수치(`neutral 95.3%`, `115.23Hz`) 확인. 이 과정에서
  `opencv-python` 버전 미고정 시 최신판(5.0.0.93)이 얼굴 검출 데이터
  파일 자체를 안 담고 있는 것을 발견해 `4.10.0.84`로 고정
  (`requirements.txt`).
  상세: `내부테스트결과서/U3b_표정음성운율분석테스트_20260908031357.md`.
- **부수적으로 발견·수정한 것**: 어제 mypy가 "클린"이라고 보고했던 게
  실제로는 mypy 캐시 때문에 `resource.setrlimit`(POSIX 전용, Windows
  mypy 기준 에러) 이슈를 놓치고 있었음 — `type: ignore` 처리로 수정.
  ⚠️ **로컬 개발 환경(사용자 공용 아나콘다) 영향 있음**: `deepface`가
  요구하는 `opencv-python-headless`가 기존에 설치돼 있던
  `opencv-python 5.0.0.93`과 충돌해, 로컬 환경의 `opencv-python`을
  `4.10.0.84`로 강제 재설치했습니다. 이 프로젝트 폴더 안에서 끝나는
  변경이 아니라 컴퓨터 전역 아나콘다 환경에 영향을 준 것이라 — 다른
  프로젝트가 opencv 5.x를 쓰고 있었다면 확인이 필요할 수 있습니다.

- **ADR-007 1단계 보안 강화 완료(2026-09-08, 사용자에게 "20년차 가이드"
  제공 후 진행 요청받음)**: seccomp로 네트워크(`socket`/`connect` 등)와
  외부 프로그램 실행(`execve`)을 차단, 비root(`nobody`) 권한 하락 추가.
  원래 계획한 네트워크 네임스페이스 분리는 Docker 기본 권한 부족으로
  실패 확인 후 더 안전한 seccomp 방식으로 대체(실측 후 판단, 추측 아님).
  **테스트 중 어제 추가한 RLIMIT_CPU가 AC-2(타임아웃 감지)를 깨고 있던
  회귀 버그도 발견·수정.** 상세:
  `내부테스트결과서/ADR007_1단계보안강화_실제exploit검증_20260908075008.md`,
  `docs/adr/adr-007-code-execution-sandbox.md` 재검토 섹션.
- [x] **`/app` 읽기전용 전환 완료(2026-09-08, 사용자 승인)**:
  `docker-compose.yml`의 `./src/backend:/app` → `:ro`로 변경(`uploads`는
  여전히 쓰기 가능하게 별도 유지). 사용자가 "이게 클로드 코드 원격제어/
  로컬서버 사용에 영향 있냐"고 질문 → **완전히 무관함을 설명**(이
  마운트는 Docker 컨테이너 내부 전용 경로이고 Claude Code는 호스트
  파일을 직접 다룸). 실제 컨테이너에서 `/app` 쓰기 차단·`/app/uploads`
  쓰기 유지·코딩 제출/미디어 업로드 전체 흐름 재검증 완료, 회귀 없음.

- **Gemini 무료 티어 일일 쿼터 소진 발견·조치(2026-09-08, 사용자 실사용
  리허설 중 발견)**: 사용자가 실제 카메라/마이크로 면접을 진행하다가
  턴 5부터 "AI 면접관 호출 실패" 반복 → 로그 확인 결과 `429
  RESOURCE_EXHAUSTED`(모델당 하루 20건 무료 한도 소진), 버그 아님.
  모델을 특정 버전 고정에서 `-latest` 별칭으로 재전환해 새 쿼터로
  즉시 재개, 429/503 메시지도 구분(`app/ai/gemini_errors.py` 신설).
  **구조적 한계로 사용자에게 알림**: 무료 티어는 모델당 하루 20건뿐이라
  실사용 리허설 1~2회로도 소진될 수 있음 — 유료 전환 여부는 사람 결정
  사항. 상세:
  `내부테스트결과서/Gemini무료티어일일쿼터소진_실사용중발견_20260908093627.md`.

- **Gemini→Groq 전환 완료(2026-09-08, 사용자 요청)**: `app/ai/llm.py`
  `GroqProvider`, `app/ai/report.py` `GroqReportGenerator` 추가(모델
  `openai/gpt-oss-120b`, 실제 키로 모델 목록/한국어 JSON 출력/레이트리밋
  확인 후 선정). Gemini 구현은 유지, `providers.py`에서 활성 구현만 교체
  — 재전환 가능. 실제 API로 회원가입~리포트 생성 전체 흐름 재검증 완료.
- **"동일 질문 반복" 실제 버그 발견·수정(같은 날, Groq 전환 검증 중)**:
  Groq로 바꿔도 동일하게 재현되어 **LLM 제공자 문제가 아니라
  `question_service.retrieve_candidates()`가 이미 나온 질문도 다시
  후보로 뽑을 수 있던 설계 결함**임을 실측으로 확인. `exclude_contents`
  파라미터 추가 + `interview_service`에서 이미 나온 AI 발화 전체를 제외
  대상으로 연결 + 시스템 프롬프트에 "후보 그대로 베끼지 말 것" 명시
  추가. 수정 전/후 실제 Groq 응답으로 비교 검증(4연속 동일 질문 →
  서로 다른 구체적 질문으로 개선, 단 "미답변 주제 재질문" 경향은
  일부 남음 — 버그 아닌 판단 영역으로 분류). pytest 52/52(신규 1건).
  상세: `내부테스트결과서/Groq전환및질문반복버그수정_20260908120348.md`.

- **⚠️ 심각한 버그 발견·수정(2026-09-08, 사용자가 "이전엔 되던 로그인이
  안 된다"고 보고해 발견)**: `tests/backend/conftest.py`의 기본
  `DATABASE_URL`이 **실제 개발 DB("aimock")를 그대로 가리키고 있어서**,
  로컬에서 `pytest` 실행할 때마다 `_clean_db` 픽스처가 전체 테이블을
  TRUNCATE — 이번 세션 내내 회귀 확인용으로 반복 실행한 pytest가 매번
  실제 회원가입 계정을 전부 삭제하고 있었음. CI는 원래부터 별도
  `aimock_test` DB를 써서 안전했음(로컬 실행에만 있던 문제). DB 이름을
  CI와 동일한 `aimock_test`로 분리하고 실제 생성+마이그레이션, pytest
  실행 전/후 개발 DB 사용자 수가 동일하게 유지됨을 실측으로 검증 완료.
  상세: `내부테스트결과서/로컬pytest가실DB를삭제하던치명적버그수정_20260908121217.md`.
  **영향받은 사용자 데이터**: 이번 세션에서 만든 테스트용 더미 계정들만
  해당(진짜 서비스 데이터 없음, 실질 피해 없음) — 단 재현 불가하니
  이후 로그인 계정은 다시 만들어야 함.

- **웹캠 프레임 검은 화면 캡처 버그 발견·수정 + 리포트 화면 재설계
  (2026-09-08, 사용자가 리포트 화면 스크린샷을 공유하며 "TRD/화면설계와
  동일한가" 질문해 발견)**: 실제 DB에 저장된 `video_frame` 미디어
  (`f43a8786-92d2-4c97-b3ae-1fdb6fba2424` 건, 14턴 전부)를 복호화해
  직접 열어본 결과 **전부 완전히 새까만 이미지**(~1.3KB, 정상이면
  ~300KB대)임을 확인 — DeepFace 문제가 아니라 캡처 자체가 실패하고
  있었음. 원인: `InterviewPage.tsx`가 화면에서 숨긴(`hidden`,
  `display:none`) `<canvas>` DOM 엘리먼트를 재사용해 프레임을 그리고
  있었는데, 이는 일부 브라우저(GPU 가속 비디오 디코드 환경)에서 빈
  화면이 캡처되는 알려진 문제와 일치. **수정**: DOM에 붙이지 않는
  인메모리 `<canvas>`를 캡처마다 새로 생성 + `video.videoWidth/Height`가
  0이면(첫 프레임 디코딩 전) 캡처를 건너뛰는 가드 추가. **한계**: 제
  테스트 환경엔 실제 카메라가 없어 이 수정이 실제로 검은 화면 문제를
  없앴는지는 코드 리뷰 수준으로만 확인했고, 실카메라 재검증은 아직
  안 됨(§4에 추적).
  같은 화면 점검에서 리포트 상세 영역이 `<pre>{JSON.stringify(...)}</pre>`로
  원본 JSON을 그대로 찍고 있던 것도 발견 — 마스터 TRD F-006이 요구하는
  "상세 피드백 리포트"에 못 미치는 개발자 디버그 수준 화면이었음(내
  자신이 작성한 프론트엔드 TRD가 리포트 화면의 시각적 레이아웃을 애초에
  규정하지 않았던 문서 공백). `src/frontend/src/components/ReportDetails.tsx`
  신설(합격 배지/STAR 분석/핵심 키워드/표정 타임라인/음성 운율을 사람이
  읽기 좋은 섹션·표로 렌더링, 지원자용·채용담당자용 화면이 공유)해
  `ReportPage.tsx`/`RecruiterReportPage.tsx`에 배선, `index.css`에
  대응 스타일 추가. `npm run build`/`lint`/`test`(16/16) 전부 통과.
- **위 발견을 계기로 한 TRD 문서 정합성 점검 및 동기화(같은 날)**:
  마스터 TRD F-006이 "음성 운율"을 요구사항에 빠뜨리고 있었고(나중에
  `aimock_u3b_trd.md`에서 신설된 필드가 반영 안 됨), "표정 타임라인은
  U3-b 미착수라 항상 빈 배열"이라는 비고가 낡아 있었으며, 프론트엔드
  TRD에는 리포트 화면의 레이아웃을 규정한 절 자체가 없어 "화면구조가
  TRD와 같은가"를 애초에 판정할 수 없는 상태였음을 확인. **문서를
  실제 구현(이미 사용자가 승인한 U3-b 착수 결정 포함)에 맞춰 동기화**
  — 이미 동작하는 기능을 문서에 없다고 화면에서 빼는 방향이 아니라
  문서를 갱신하는 방향으로 처리(요구사항 후퇴 아님, 문서 갱신 누락
  이었을 뿐). `aimock_master_trd.md` F-006 행 갱신,
  `aimock_frontend_trd.md`에 **§1-1(리포트 화면 as-built 구조)** 신설 +
  **AC-F11** 추가(원본 JSON 미노출 + 정해진 섹션 순서 검증 가능하게
  명문화) + §0의 낡은 "U3-b 보류" 문구 정정. Claude Browser로 실제
  로그인해 문제의 그 리포트 화면을 다시 열어 AC-F11 PASS 확인(스크린샷
  근거). 상세:
  `내부테스트결과서/리포트화면TRD정합성점검및문서동기화_20260908124216.md`.

- **⚠️ 실제 버그 발견·수정: `created_at` 컬럼이 전부 고정 리터럴로
  굳어있던 문제(2026-09-08, 전체 화면 TRD 실측 테스트 중 "원본 답변
  오디오 관리" 목록의 시각 표시가 이상해서 발견)**: `users`/
  `media_assets`/`coding_submissions`/`evaluation_reports`/
  `whiteboard_snapshots` 5개 테이블의 `created_at` DEFAULT가 함수 호출
  `now()`가 아니라 **최초 `alembic upgrade head` 실행 시각
  (2026-09-07 12:30:31.422073+00)으로 고정된 리터럴**이었음 — 원인은
  SQLAlchemy `server_default="now()"`를 순수 Python 문자열로 준 것
  (`text("now()")`로 명시해야 함). 방금 이 세션에서 새로 가입한 계정도
  이 고정값으로 찍히는 것으로 실증. 기능적 영향은 없음(이 컬럼들로
  정렬/판단하는 로직 없음, 유일하게 정렬에 쓰이는 `Transcript.created_at`
  은 이미 다른 이유로 Python 콜러블 기본값이라 안전했음)이나, 화면에
  잘못된 생성 시각을 노출하는 표시 버그. 모델 5개 파일 수정 +
  신규 마이그레이션(`f6341f660dd1`)으로 라이브 DB 컬럼 DEFAULT만 교정
  (**기존 저장된 값은 재작성하지 않음**, 되돌리기 어려운 결정 회피).
  신규 가입 계정으로 수정 검증 완료(생성시각-DB현재시각 0.6초 이내
  일치), pytest 52/52 회귀 없음. 이 과정에서 job_role이 질문 주제를
  실제로 바꾼다는 것(카테고리 필터 아님, LLM 프롬프트 컨텍스트 효과)도
  직접 실측으로 확인. 상세:
  `내부테스트결과서/전체TRD화면실측및질문개수직무필터점검_20260908132406.md`.

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
| 리포트 생성 409는 "이미 생성 중"을 의미할 것(프론트 작성 시 AI의 추정) | 실제로는 `report_service.generate_report()`의 유일한 409 조건이 "면접이 아직 completed 상태가 아님"이었음 — "생성 중" 상태 자체가 백엔드에 없음 | `ReportPage.tsx`가 서버의 실제 `error.message`를 그대로 노출하도록 수정(하드코딩 문구 제거), 브라우저로 재검증 완료 |
| Claude Browser 자동화 도구로 `<input type="file">`에 실제 파일을 주입할 수 있을 것 | 브라우저 보안 정책상 `HTMLInputElement.value`를 파일명으로 프로그램적으로 설정 불가(`InvalidStateError`) — 도구 한계, 앱 버그 아님 | AC-F6의 오디오 업로드는 curl로 프론트와 동일한 multipart 필드명(`turn_index`/`audio`)을 실제 백엔드에 보내 계약만 검증, UI 클릭 종단 검증은 실제 사람이 마이크로 확인 필요 |
| `server_default="now()"`(Python 문자열)을 주면 SQLAlchemy가 매 INSERT마다 실제 DB 함수 `now()`를 호출할 것 | 실제로는 DDL에 그 마이그레이션을 처음 적용한 시각의 **고정 리터럴**로 굳어버림 — `users`/`media_assets`/`coding_submissions`/`evaluation_reports`/`whiteboard_snapshots` 전부 영향받아, 오늘 새로 가입한 계정마저 어제 시각으로 찍혀 있었음 | `text("now()")`로 함수 호출임을 명시 + 신규 마이그레이션으로 라이브 DB 컬럼 DEFAULT만 교정(기존 값은 유지) |
| `display:none`(hidden) `<canvas>`에 `drawImage`로 비디오 프레임을 그려도 정상 캡처될 것 | 실제 사용자 리허설에서 저장된 14개 프레임이 전부 완전히 검은 이미지(~1.3KB)였음 — 일부 브라우저의 GPU 가속 디코드 경로에서 숨긴 캔버스에 빈 화면이 그려지는 알려진 문제 | DOM에 붙이지 않는 인메모리 `<canvas>`를 캡처마다 새로 생성 + `videoWidth/Height===0` 가드로 교체(`InterviewPage.tsx`). **실카메라 재검증은 아직 미완료**(§4) |
| 프론트엔드 TRD가 화면 레이아웃까지 규정했을 것(작성 당시 스스로의 가정) | 실제로는 라우트/API 매핑/에러 분기만 있고 리포트 화면의 시각적 구조(섹션 순서, 표 형태 등)를 규정한 절이 없어 "TRD와 화면이 같은가"를 판정할 기준이 부재했음 | `aimock_frontend_trd.md`에 §1-1(as-built 리포트 화면 구조) 신설 + AC-F11 추가로 향후 비교 가능하게 함 |

## §4. 남은 것 / 다음 세션에서 할 일
- [x] 마스터 TRD §2(기능요구사항)/§3(비기능요구사항) 표 내용을 AI가
  실제 코드와 대조해 라인별 검토 완료(2026-09-08) —
  `docs/trd/aimock_master_trd_review_20260908.md`. **사람의 최종
  승인/반려는 아직 안 남** — 문서 내 "사람이 결정할 것" 3개 확인 필요
- [x] §6의 미결 정책 2건 확정 — 2026-09-07: 원본 미디어는 지원자 삭제
  요청 전까지 암호화 보관(ADR-004), 계정 탈퇴는 소프트삭제+30일 유예
  자동파기(ADR-006)
- [x] U1(인증/계정+탈퇴) + U1-b(미디어 저장+삭제) 구현 및 AC 12/12 검증
  완료 (2026-09-07)
- [x] U2-a(턴 기반 질문-답변) + U3-a(STT/LLM 파이프라인) 구현 및 AC 11/11
  검증 완료(자동화 10 + 수동 1) (2026-09-07)
- [x] U2-b(라이브 코딩) 구현 및 AC 7/7 검증 완료 (2026-09-07) — ⚠️
  ADR-007 보안 한계(공개 배포 전 재검토 필수) 반드시 인지
- [x] U4(피드백 리포트) 구현 및 AC 8/8 검증 완료 (2026-09-07)
- [x] U5(채용담당자 대시보드) 구현 및 AC 6/6 검증 완료 (2026-09-07)
  → **Must-have 단위 전체 완료**
- [x] 프론트엔드(React/Vite) 전체 화면 구현 및 AC-F 9/10 검증 완료
  (2026-09-07) — 나머지 1개(AC-F6)는 GEMINI_API_KEY 확보 후 재검증 필요.
  **2026-09-08 AC-F11 신설 및 PASS 확인**(리포트 화면 구조화 표시,
  §2 최신 항목) — 총 10/11
- [x] 프로덕션 강화 8건 + 원본 오디오 미보관 버그/AC-M6 UI 부재 발견·수정
  완료(2026-09-08) — pytest 47/47, 프론트 vitest 16/16
- **사람의 diff 리뷰는 U1/U1-b/U2-a/U3-a/U2-b/U4/U5/프론트엔드/프로덕션
  강화 8건 전부 아직 없음** (harness_00_overview §4 규칙 3 "리뷰 필수").
  git 커밋/브랜치/PR은 CLAUDE.md 금지 규칙에 따라 AI가 하지 않음 —
  사용자가 직접 커밋해야 함.
- [ ] **다음으로 사람이 결정할 것(AI가 자동으로 진행할 수 없는 지점)**:
  1. [x] `GEMINI_API_KEY` 확보·반영 완료(2026-09-08, 사용자 제공) — 실제
     Gemini로 면접 질문 생성/리포트 채점까지 검증 완료(아래 §2 최신
     항목). 남은 건 프론트엔드 AC-F6(브라우저 마이크로 실사용)만 사람이
     직접 시연.
  2. [x] U3-b(표정/음성분석) **엔진 + 실시간 웹캠 캡처 UI 모두 완료**
     (2026-09-08, 사용자가 실제 샘플 제공 후 UI까지 추가 요청) —
     DeepFace/librosa 어댑터 + 리포트 배선 + `InterviewPage.tsx`의 자동
     프레임 캡처(턴마다 1장, 별도 조작 불필요) 완료. 실제 샘플로 AC 5/5
     검증, 카메라 없는 환경 폴백도 확인. —
     `내부테스트결과서/U3b_실시간웹캠캡처UI테스트_20260908060038.md` 참조.
     **[ ] 남은 것(사람 확인 필요, 아직 미완료)**: 실사용 리허설에서
     캡처된 프레임이 전부 검은 화면이었던 버그를 발견·수정했음(인메모리
     캔버스 교체, §2 최신 항목). **실제 웹캠이 달린 브라우저로 면접을
     1건 진행해 표정 타임라인이 "unknown"이 아닌 실제 감정으로 나오는지
     사용자님이 직접 재확인해주셔야 함** — 자동화 도구엔 카메라 장치가
     없어 코드 리뷰 수준 검증만 가능했음.
  3. [x] U2-c(화이트보드, Could): **스킵 확정**(2026-09-08 사용자 결정,
     MVP는 이미 충분히 완성도 있다고 판단).
  4. [x] `docs/trd/aimock_master_trd_review_20260908.md`의 라인별 검토
     결과 **승인 완료**(2026-09-08) — "문서를 실제 구현에 맞게 정정"
     방식으로 처리, `docs/trd/aimock_master_trd.md` §2/§3에 "실제 구현
     상태" 열 추가 반영 완료(v0.2).
  5. ADR-007 B안(Piston)/C안(Docker-in-Docker) 전환: **미확정, 다만
     "향후 공개 배포 가능성 있음"을 사용자가 명시적으로 확인**(2026-09-08)
     — 실제 공개 배포 결정 시점에는 A안 그대로 배포 금지, 반드시 재논의
     먼저 거칠 것(ADR-007 재검토 섹션 참조).
  4. **전체 코드에 대한 diff 리뷰 + git 커밋** — 지금 워킹트리에 커밋
     안 된 파일이 많이 쌓여 있음(백엔드+프론트엔드 전체).

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
- 프론트엔드 실행: `cd src/frontend && npm install && npm run dev`
  (포트 5173, `.env.example` 참고해 `.env` 생성). 백엔드가 8000번으로
  떠 있어야 하고, CORS는 `main.py`에서 5173만 허용하도록 설정돼 있음.
- `harness_00_overview.md` §6 품질 게이트 체크리스트를 매 단위 완료 시
  실제로 확인했는지.

## §6. 리스크/미결 정책 (아직 사람의 최종 결정이 안 난 것)

| 항목 | 상태 |
|---|---|
| 원본 오디오/비디오 영구 저장 여부 (ADR-004) | **확정** — 지원자 삭제 요청 전까지 암호화 보관 |
| 계정 탈퇴 시 데이터 처리 (ADR-006) | **확정** — 소프트삭제 + 30일 유예 후 스케줄러 자동 물리삭제 |
| 30일 유예기간 값의 법무적 타당성 | 미확정(AI 제안 기본값) — MVP 범위에서는 그대로 진행, 실서비스 전환 시 재검토 필요 |
| Gemini 무료 티어 쿼터 소진 시 대응(Groq 전환) | 방향은 확정(ADR-002), 구현 전 최종 확인 필요 |
