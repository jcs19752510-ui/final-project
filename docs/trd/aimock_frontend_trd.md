# 프론트엔드 통합 TRD — 웹 AI 모의면접 플랫폼 (React/Vite)

> `harness/harness_01_trd_template.md` 형식을 프론트엔드 전체 스코프에
> 맞게 적용. 상위 문서: `docs/trd/aimock_master_trd.md` §1(화면 목록).
> **문서 코드 판단 근거**: 화면(U1/U2-a/U2-b/U4/U5)마다 별도 TRD를 새로
> 쪼개지 않고 하나로 묶은 이유는 라우팅/인증 컨텍스트/API 클라이언트/
> 디자인 토큰이 전체 SPA에서 공유되는 하나의 응집된 엔지니어링 단위이기
> 때문(20년차 판단, `자동진행/프론트엔드TRD통합및착수결정_20260907232301.md` 참조).
> 파일명은 마스터 TRD/A0 인수인계와 같은 "단위 코드 없는 전체 문서"
> 패턴(`master`/`a0`)을 따라 `frontend`를 코드 자리에 사용
> (`docs/tech_conventions.md` §하네스 문서 파일명 규칙 예외 해석).

## 문서 정보
- 프로젝트: aimock
- 단위(화면/기능) 이름: 프론트엔드 SPA 전체 (U1/U2-a/U2-b/U4/U5 화면)
- 작성일 / 버전: 2026-09-07 / v0.1
- 상태: 확정 (자동진행으로 착수 — 사용자가 "긴급/본인 처리 아니면 자동
  진행" 명시적으로 승인)

## §0. 범위 및 흐름 개요
- 역할: 이미 구현·검증 완료된 백엔드 API(U1/U1-b/U2-a/U2-b/U3-a/U4/U5,
  pytest 43/43 pass)를 호출하는 React SPA. 새 백엔드 기능/엔드포인트는
  추가하지 않는다(스코프 준수 — 하네스 원칙 1).
- 화면 목록 (라우트):
  | 라우트 | 화면 | 대응 백엔드 단위 |
  |---|---|---|
  | `/login`, `/signup` | 로그인/회원가입 | U1 |
  | `/interview/:id` | 면접장(턴 기반 질문-답변 + 녹음) | U2-a, U3-a |
  | `/interview/:id/coding` | 라이브 코딩(Python) | U2-b |
  | `/report/:id` | 피드백 리포트(지원자용) | U4 |
  | `/dashboard` | 채용담당자 대시보드 | U5 |
- 인증: 로그인 성공 시 JWT를 저장(XSS 위험 최소화를 위해 `localStorage`
  대신 메모리 변수 + `sessionStorage` 백업 — 새로고침 시 재로그인 요구는
  MVP 범위에서 허용, 판단 근거 §7 기록)하고, 모든 API 호출에
  `Authorization: Bearer` 헤더로 첨부.
- 의존: 백엔드가 `docker compose up -d`로 기동되어 있어야 함
  (`http://localhost:8000` 또는 `.env`의 `VITE_API_BASE_URL`).
- U2-c(화이트보드)는 Could/보류 상태라 화면에서 "준비 중" 플레이스홀더만
  두고 실제 캔버스 구현은 하지 않는다(release_plan.md §1 그대로 계승).
- **U3-b(표정/음성 타임라인)는 2026-09-08 사용자 결정으로 착수·구현
  완료**(`docs/trd/aimock_u3b_trd.md`). 위 문장의 "보류" 상태는 이 문서
  작성 시점(2026-09-07) 기준이며 더 이상 유효하지 않다 — 실제 화면
  구조는 §1-1 참조.

## §0-1. 비기능 요구사항 체크
- 접근성: 폼 입력에 `label` 연결, 버튼에 명확한 텍스트(아이콘만 사용 금지).
- 에러 처리: 모든 API 호출은 `{error:{code,message}}` 포맷을 파싱해
  사용자에게 `message`를 그대로 노출(백엔드가 이미 사용자용 메시지로
  작성 — `docs/tech_conventions.md` API 규약).
- 로딩 상태: 네트워크 호출 중 버튼 비활성화 + 스피너, 이중 제출 방지.
- 개인정보 보호(하네스 원칙 7): 테스트 계정은 `test+*@example.com` 등
  샘플 이메일만 사용, 실제 개인정보 입력 금지.
- 브라우저 지원: 최신 Chrome 기준(MediaRecorder API 필요, 1인/4주
  규모라 폴리필/구형 브라우저 대응은 Won't).

## §1. 화면/상태 구조
- 공통: `src/frontend/src/api/client.ts`(fetch 래퍼, JWT 첨부 +
  에러 파싱 공통화), `src/frontend/src/state/AuthContext.tsx`(로그인
  상태 전역 관리, `role`로 지원자/채용담당자 라우팅 분기).
- 화면별 로컬 상태는 각 페이지 컴포넌트 내부에서만 관리(전역 상태 라이브러리
  Redux 등은 이 규모에 과함 — React Context로 충분, ADR 대상 아님).

## §1-1. 리포트 화면 상세 구조 (사후 기록 — 2026-09-08)

> 이 절은 착수 전 설계가 아니라 **구현 후 실제 구조를 문서에 반영한
> as-built 기록**입니다(20년차 판단 근거: 사용자가 실제 리포트 화면을
> 보고 "TRD와 화면구조/내용이 동일한가"를 물었을 때, 화면설계서가
> 아예 없어 비교 자체가 불가능했던 문서 공백을 발견 →
> `docs/trd/aimock_master_trd.md` F-006과 맞춰 이 절을 신설). 이후
> 리포트 화면을 변경할 때는 이 절도 함께 갱신한다.

- 대상 화면: `/report/:id`(지원자용, `ReportPage.tsx`),
  `/dashboard/report/:id`(채용담당자용, `RecruiterReportPage.tsx`).
  두 화면 모두 상세 영역은 공용 컴포넌트
  `src/frontend/src/components/ReportDetails.tsx`를 그대로 재사용한다
  (동일한 `details_json` 구조를 쓰므로 중복 구현 금지 — 하네스 원칙
  "중복 방지").
- 화면 상단(공통, `ReportDetails` 바깥): 역량별 점수 배지
  3종(기술/커뮤니케이션/조직 적합성, `ScoreBadge`) → "요약"(`summary_text`)
  순으로 배치. F-006 범위가 아니라 F-007(적합도 스코어링)에 대응.
- `ReportDetails` 내부 렌더 순서(위→아래, `details_json` 키 기준):
  1. `pass_recommendation`(boolean) → 합격 추천/합격 보류 배지(F-007)
  2. `star_analysis`(string) → "STAR 분석" 섹션, 자유 텍스트 문단
  3. `keywords`(string[]) → "핵심 키워드" 섹션, 태그 목록
  4. `emotion_timeline`(턴별 `{turn_index, dominant_emotion, confidence}`)
     → "표정 타임라인" 섹션, 표(턴/표정/신뢰도). 전 턴이 `unknown`이면
     "캡처된 프레임 N장에서 표정을 인식하지 못했습니다" 안내 문구를
     표 위에 추가 표시(원인 미상의 빈 결과를 사용자가 오해하지 않도록).
     한글 라벨 매핑은 `EMOTION_LABELS` 상수 참조.
  5. `voice_prosody`(턴별 `{turn_index, pitch_mean_hz, energy_mean}`)
     → "음성 운율" 섹션, 표(턴/평균 피치(Hz)/발화 에너지). 값이 0이면
     "-"로 표시(무음 구간 등 분석 실패 시 0 반환 — `app/ai/prosody.py`).
  6. 각 섹션은 해당 배열/문자열이 비어 있으면(예: 리포트 생성 당시
     media 없음) 렌더링을 생략한다(빈 제목만 남는 것 방지).
- 원본 JSON을 그대로 화면에 노출하는 `<pre>{JSON.stringify(...)}</pre>`
  방식은 2026-09-08부로 완전히 제거됨(이전 방식 — 개발자 디버그 수준,
  F-006이 요구하는 "상세 피드백 리포트"에 미달로 판단해 교체).
- 면접장(`/interview/:id`) 화면의 표정 프레임 캡처: 카메라 미리보기는
  화면 우상단에 작은 비디오(`160×120px`, 좌우 반전 표시)로 상시 노출,
  답변 제출 시마다 그 순간 프레임 1장을 자동 캡처해
  `POST /interviews/{id}/media`(`kind=video_frame`)로 업로드한다.
  캡처는 화면에 보이지 않는(DOM 밖) `<canvas>`를 매번 새로 생성해
  사용하며, `video.videoWidth/videoHeight`가 0이면(첫 프레임 디코딩
  전) 캡처를 건너뛰고 다음 턴에 재시도한다(2026-09-08 버그 수정 —
  이전에는 화면에서 숨긴 `<canvas hidden>`을 재사용해 일부 브라우저에서
  캡처 결과가 완전히 검은 화면으로 나오는 문제가 있었음).

## §2. 화면/API 매핑 명세

| 화면 | 호출 API | 비고 |
|---|---|---|
| 로그인 | `POST /api/v1/auth/login` | 성공 시 role에 따라 `/dashboard`(recruiter) 또는 지원자 홈으로 이동 |
| 회원가입 | `POST /api/v1/auth/signup` | 성공 후 자동 로그인 처리(가입 폼에서 바로 login 재호출) |
| 내 정보/탈퇴 | `GET /auth/me`, `POST /auth/withdraw` | 탈퇴 시 확인 모달(되돌리기 어려운 화면 액션 — 반드시 confirm) |
| 면접장 | `POST /interviews`, `POST /interviews/{id}/turns`(MediaRecorder로 녹음 후 업로드), `POST /interviews/{id}/end` | 정확한 API 경로는 `src/backend/app/api/routes/`의 실제 라우터 기준(원본 우선 원칙 — TRD 문구와 실제 코드가 다르면 실제 코드를 따른다) |
| 라이브 코딩 | `POST /interviews/{id}/coding` (Monaco 에디터로 코드 작성 후 제출) | 5초 타임아웃 UX 안내 문구 필수(ADR-007 보안 한계 사용자 인지) |
| 리포트 | `GET /reports/{interview_id}` | 생성 전(404)/생성 중(409)/미설정 키(503) 상태별 안내 메시지 분기 |
| 대시보드 | `GET /recruiter/candidates`, `GET /recruiter/reports/{id}`, `GET /recruiter/stats` | recruiter 역할 아니면 403 → 접근 차단 안내 |

> 실제 엔드포인트 경로는 구현 착수 시 `src/backend/app/api/routes/*.py`를
> 다시 읽어 확정한다(§6 테스트 시나리오에서 curl로 재확인 예정).

## §3. 워크플로우 및 비즈니스 로직
- 인증 가드: `AuthContext`에 토큰 없으면 보호된 라우트 접근 시 `/login`으로
  리다이렉트.
- 역할 가드: `role=candidate`는 `/dashboard` 접근 시 프론트에서도 차단(백엔드
  403과 이중 방어, UX상 에러 화면 대신 접근 자체를 안 보여줌).
- 면접 턴 흐름: 녹음 시작 → 정지 → 업로드(스피너) → 다음 질문 표시 →
  마지막 질문 후 "면접 종료" 버튼 활성화.

## §4. 상태/에러 코드
백엔드 §4(각 단위 TRD)를 그대로 계승. 프론트는 HTTP 상태코드별 사용자
메시지만 매핑(예: 503 → "AI 채점 서비스가 일시적으로 사용 불가합니다").

## §5. 인수 조건 (Acceptance Criteria)
- [ ] AC-F1: 신규 이메일로 회원가입 화면에서 가입하면 자동 로그인되어
  지원자 홈으로 이동한다.
- [ ] AC-F2: 잘못된 비밀번호로 로그인 시도 시 화면에 에러 메시지가
  표시되고 페이지가 멈추거나 깨지지 않는다.
- [ ] AC-F3: 로그인 없이 `/dashboard`에 직접 접근하면 `/login`으로
  리다이렉트된다.
- [ ] AC-F4: 지원자 계정으로 `/dashboard` 접근 시 접근이 차단된다(화면
  자체가 안 보이거나 명확한 안내 문구).
- [ ] AC-F5: 탈퇴 버튼 클릭 시 확인 모달이 뜨고, 확인해야만 실제
  `/auth/withdraw`가 호출된다(실수 방지).
- [ ] AC-F6: 면접장 화면에서 텍스트 답변 제출(또는 오디오 업로드 mock)이
  성공하면 다음 질문으로 화면이 갱신된다.
- [ ] AC-F7: 라이브 코딩 화면에서 Python 코드를 제출하면 실행 결과(stdout
  또는 에러)가 화면에 표시된다.
- [ ] AC-F8: 리포트 미생성 상태에서 리포트 화면 접근 시 404에 대응하는
  안내 문구가 표시된다(빈 화면/콘솔 에러 아님).
- [ ] AC-F9: 채용담당자 대시보드에서 지원자 목록이 표시되고, 항목 클릭
  시 해당 리포트로 이동한다.
- [ ] AC-F10: `npm run build`(TypeScript 컴파일 포함)가 에러 없이
  성공한다.
- [ ] AC-F11(2026-09-08 추가): 리포트 화면(`/report/:id`,
  `/dashboard/report/:id`)에 원본 JSON이 노출되지 않고, §1-1에 정의한
  순서(합격 배지 → STAR 분석 → 핵심 키워드 → 표정 타임라인 → 음성
  운율)대로 구조화되어 표시된다. 표정/음성 데이터가 없는 리포트는
  해당 섹션이 생략된다.

## §6. 테스트 시나리오
- 실제 브라우저(Claude Browser 도구)로 `docker compose`로 띄운 실제
  백엔드에 대해 화면 조작 → 각 AC 1:1 대응 시나리오 실행 후
  `내부테스트결과서/`에 스크린샷 근거와 함께 기록(하네스 원칙 4 자기검증).
- U2-a/U3-a는 `GEMINI_API_KEY` 미확보 상태이므로 LLM 응답 관련 화면은
  503 처리 경로로 검증(자동진행 판단 유지, `docs/handoff/aimock_a0_handoff.md`
  §4 항목 1과 동일 제약).

## §7. 미결 항목 / 판단 근거
| 항목 | 채택한 기본값 | 근거 |
|---|---|---|
| 토큰 저장 위치 | `sessionStorage`(새로고침 시 유지, 탭 닫으면 소멸) | localStorage보다 XSS 노출 창을 줄이면서도 새로고침마다 재로그인해야 하는 불편은 피함 — MVP 데모 목적에 적합 |
| CSS 프레임워크 | 별도 라이브러리 없이 최소 CSS(styled-jsx/Tailwind 등 미도입) | 4주/1인 규모에서 빌드 설정 추가 리스크 대비 이득이 낮음, ADR 대상 아님(가역적 결정) |
| 상태관리 라이브러리 | React Context + useState만 사용 | 화면 5개 규모에 Redux 등은 과함 |
