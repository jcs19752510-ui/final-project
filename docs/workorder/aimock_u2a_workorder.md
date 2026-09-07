# 작업지시서 — U2-a(턴 기반 질문-답변) + U3-a(STT/LLM 파이프라인)

> `harness/harness_02_work_order_template.md` 형식. U1+U1-b와 같은 이유로
> 두 단위를 한 세션에 묶음(release_plan.md Week2가 이미 이렇게 묶어둠).

## 문서 정보
- 프로젝트/단위: aimock / U2-a + U3-a
- 참조 TRD: `docs/trd/aimock_u2a_trd.md`, `docs/trd/aimock_u3a_trd.md`
- 작성일: 2026-09-07

## §0. 전제 조건
- 완료: U1(인증), U1-b(미디어) — 완료 및 AC 12/12 검증됨.
- 참고: `docs/adr/adr-002-ai-pipeline-stack.md`(LLM/STT 선택 근거).

## §1. 이번 단계 범위
- [x] `LLMProvider`/`STTProvider` 인터페이스 + `GeminiProvider`/
  `FasterWhisperProvider` 실제 구현 + 테스트용 Fake 구현
- [x] `questions` 시드 데이터(샘플 10문항) + `retrieve_candidates()`
- [x] interview 생성/턴 제출/종료 API (U2-a §2)
- [x] pytest(Fake Provider 주입) + 실제 faster-whisper 수동 스모크테스트
  + 결과를 `내부테스트결과서/`에 기록

## §2. 안 하는 것 (Out of Scope)
- 실제 Gemini API 호출(키 미확보) — 코드는 완성하되 실행은 사용자가 키
  발급 후 수행.
- 임베딩 기반 벡터 검색 — TRD §7 미결, category/difficulty 필터로 대체.
- 프론트엔드 화면 — 백엔드 API까지만.
- 코딩 IDE/화이트보드(U2-b/U2-c) — 다음 단위.

## §3. 착수 전 확정 정책
| 미결 항목 | 권장 기본값 | 이번 세션 적용 여부 |
|---|---|---|
| 답변 길이 제한 | 800자 | 적용 |
| faster-whisper 모델 크기 | tiny | 적용 |
| RAG 검색 방식 | category/difficulty 필터(임베딩 아님) | 적용 |

## §4. 완료 후 받을 결과물
- [x] 소스 코드(`src/backend/app/ai/`, `app/services/interview_service.py` 등)
- [x] 테스트 결과 로그 + AC pass/fail 표 → `내부테스트결과서/`
- [x] 판단 근거 요약(A0에 기록)
- [x] 발견된 편차(A0 §3)

## §5. 프롬프트
> 이번 세션이 곧 실행 세션이므로 harness_04 프롬프트 생성 절차는 생략.

## §6. 다음 단계 예고
- 다음 단위: U2-b(라이브 코딩) 또는 U4(리포트) — 릴리스 계획 §4 순서상
  Week3 진입 전에 U2-a/U3-a AC가 전부 pass인지 재확인 후 결정.
