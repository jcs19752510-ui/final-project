# 작업지시서 — U5(채용담당자 대시보드)

> `harness/harness_02_work_order_template.md` 형식.

## 문서 정보
- 프로젝트/단위: aimock / U5
- 참조 TRD: `docs/trd/aimock_u5_trd.md`
- 작성일: 2026-09-07

## §0. 전제 조건
- 완료: U1, U1-b, U2-a, U3-a, U2-b, U4 (전부 AC 검증 완료).

## §1. 이번 단계 범위
- [x] `require_recruiter` 인증 의존성
- [x] 목록/리포트열람/통계 API
- [x] pytest + 결과를 `내부테스트결과서/`에 기록

## §2. 안 하는 것 (Out of Scope)
- 프론트엔드 대시보드 화면.
- 질문지 커스터마이징 — 마스터 TRD에 없는 기능(Won't).
- 페이지네이션 — MVP 범위 밖.

## §3. 착수 전 확정 정책
| 미결 항목 | 권장 기본값 | 이번 세션 적용 여부 |
|---|---|---|
| 목록 크기 제한 | 없음(전체 반환) | 적용 |

## §4. 완료 후 받을 결과물
- [x] 소스 코드(`src/backend/app/services/recruiter_service.py` 등)
- [x] 테스트 결과 로그 + AC pass/fail 표 → `내부테스트결과서/`
- [x] 판단 근거 요약(A0 반영)

## §5. 프롬프트
> 작성 세션이 곧 실행 세션 — harness_04 절차 생략.

## §6. 다음 단계 예고
- Must-have 단위(U1~U5) 전부 완료 예정. 다음은 Could-have인
  U2-c(화이트보드)나 QA/통합테스트, 또는 사람이 확보한 자료(웹캠 샘플,
  GEMINI_API_KEY)로 U3-b/실제 LLM 검증.
