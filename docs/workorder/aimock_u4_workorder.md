# 작업지시서 — U4(피드백 리포트)

> `harness/harness_02_work_order_template.md` 형식.

## 문서 정보
- 프로젝트/단위: aimock / U4
- 참조 TRD: `docs/trd/aimock_u4_trd.md`
- 작성일: 2026-09-07

## §0. 전제 조건
- 완료: U1, U1-b, U2-a, U3-a, U2-b (전부 AC 검증 완료).

## §1. 이번 단계 범위
- [x] `ReportGenerator` 어댑터(Gemini/Fake) + 로컬 키워드 추출기
- [x] 리포트 생성/조회 API + `evaluation_reports` upsert
- [x] pytest(Fake Generator) + 결과를 `내부테스트결과서/`에 기록

## §2. 안 하는 것 (Out of Scope)
- 표정/음성 타임라인 — U3-b 미착수(자동진행 판단).
- 채용담당자 열람 화면 — U5.
- 실제 Gemini 호출 검증 — `GEMINI_API_KEY` 미확보.

## §3. 착수 전 확정 정책
| 미결 항목 | 권장 기본값 | 이번 세션 적용 여부 |
|---|---|---|
| 키워드 개수 | 상위 5개 | 적용 |
| 재생성 시 처리 | upsert(덮어쓰기) | 적용 |

## §4. 완료 후 받을 결과물
- [x] 소스 코드(`src/backend/app/services/report_service.py` 등)
- [x] 테스트 결과 로그 + AC pass/fail 표 → `내부테스트결과서/`
- [x] 판단 근거 요약(A0 반영)

## §5. 프롬프트
> 작성 세션이 곧 실행 세션 — harness_04 절차 생략.

## §6. 다음 단계 예고
- 다음 단위: U5(대시보드) — 채용담당자가 U4 리포트를 열람하는 화면/API.
