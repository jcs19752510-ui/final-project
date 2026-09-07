# 작업지시서 — 프론트엔드(React/Vite) 전체 화면

> `harness/harness_02_work_order_template.md` 형식.

## 문서 정보
- 프로젝트/단위: aimock / 프론트엔드(U1/U2-a/U2-b/U4/U5 화면)
- 참조 TRD: `docs/trd/aimock_frontend_trd.md`
- 작성일: 2026-09-07

## §0. 전제 조건
- 완료: 백엔드 U1/U1-b/U2-a/U3-a/U2-b/U4/U5 전부(pytest 43/43 pass).
- 실제 API 경로/스키마는 `src/backend/app/api/routes/*.py`,
  `src/backend/app/schemas/*.py`를 직접 읽어 확인함(원본 우선 원칙) —
  TRD §2 표와 100% 일치 확인 완료.

## §1. 이번 단계 범위
- [ ] `src/frontend/` Vite+React+TypeScript 스캐폴드
- [ ] 백엔드 `main.py`에 CORS 미들웨어 추가(프론트 dev 서버 5173 → 백엔드
  8000 크로스오리진 호출 허용 — 새 기능이 아니라 이미 정의된 프론트-백엔드
  연결에 필요한 최소 인프라 배선, 스코프 위반 아님)
- [ ] 공통: `api/client.ts`(JWT 첨부 + 에러 파싱), `state/AuthContext.tsx`
- [ ] U1: 로그인/회원가입/탈퇴 화면
- [ ] U2-a/U3-a: 면접장(턴 기반 질문-답변, MediaRecorder 녹음)
- [ ] U2-b: 라이브 코딩(Monaco 에디터)
- [ ] U4: 피드백 리포트 화면
- [ ] U5: 채용담당자 대시보드
- [ ] 실제 브라우저(Claude Browser 도구)로 AC-F1~F10 전부 수동 검증 →
  `내부테스트결과서/`에 기록
- [ ] `docs/handoff/aimock_a0_handoff.md` 갱신

## §2. 안 하는 것 (Out of Scope)
- U2-c(화이트보드) 실제 캔버스/Vision 연동 — "준비 중" 플레이스홀더만.
- U3-b(표정/음성) 실제 타임라인 시각화 — 빈 배열 대응 안내 문구만.
- 반응형/모바일 최적화, 다국어(i18n) — MVP 데모 목적 밖(Won't).
- E2E 자동화 테스트 프레임워크(Playwright 등) 도입 — 수동 브라우저 검증으로
  대체(1인/4주 규모에서 도구 도입 비용 대비 이득 낮음).

## §3. 착수 전 확정 정책
| 미결 항목 | 권장 기본값 | 이번 세션 적용 여부 |
|---|---|---|
| JWT 저장 위치 | sessionStorage | 적용 |
| CSS 방식 | 순수 CSS(별도 프레임워크 없음) | 적용 |
| 코드 에디터 | `@monaco-editor/react` | 적용 |
| 라우팅 | `react-router-dom` v6 | 적용 |

## §4. 완료 후 받을 결과물
- [ ] 소스 코드(`src/frontend/`)
- [ ] 테스트 결과(AC-F1~F10 pass/fail) → `내부테스트결과서/`
- [ ] 판단 근거 요약(A0 반영)
- [ ] 발견된 편차(A0 §3)

## §5. 프롬프트
> 작성 세션이 곧 실행 세션 — harness_04 절차 생략. 사용자가 이번 세션
> 자동진행을 명시적으로 승인(2026-09-07).

## §6. 다음 단계 예고
- 완료 후 사용자에게 diff 리뷰 + git 커밋 요청.
- `GEMINI_API_KEY` 확보 시 U2-a/U3-a/U4의 실제 LLM 응답 화면 재검증 필요.
