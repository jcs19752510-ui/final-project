# 작업지시서 — U2-b(라이브 코딩)

> `harness/harness_02_work_order_template.md` 형식.

## 문서 정보
- 프로젝트/단위: aimock / U2-b
- 참조 TRD: `docs/trd/aimock_u2b_trd.md`
- 작성일: 2026-09-07

## §0. 전제 조건
- 완료: U1, U1-b, U2-a, U3-a (전부 AC 검증 완료).
- 참고: `docs/adr/adr-007-code-execution-sandbox.md`(보안 한계 필독).

## §1. 이번 단계 범위
- [x] `CodeExecutor` 인터페이스 + `SubprocessExecutor` 실제 구현
- [x] 코드 제출 API + `coding_submissions` 저장
- [x] pytest(실제 subprocess 실행, mock 없음) + 결과를 `내부테스트결과서/`에 기록

## §2. 안 하는 것 (Out of Scope)
- JavaScript 등 Python 이외 언어 — Won't(마스터 TRD 원칙).
- AI 코드 평가(정답여부/시간복잡도/스타일) — U4로 이동(자동진행 판단).
- 프론트엔드(Monaco 에디터) 화면.
- 진짜 격리 샌드박스(Piston/Docker-in-Docker) — ADR-007에서 이미 보류
  결정, 공개 배포 시점 전까지 재검토 안 함.

## §3. 착수 전 확정 정책
| 미결 항목 | 권장 기본값 | 이번 세션 적용 여부 |
|---|---|---|
| 실행 타임아웃 | 5초 | 적용 |
| 지원 언어 | Python만 | 적용 |
| 자식 프로세스 환경변수 | PATH만 전달 | 적용 |

## §4. 완료 후 받을 결과물
- [x] 소스 코드(`src/backend/app/sandbox/`, `app/services/coding_service.py` 등)
- [x] 테스트 결과 로그 + AC pass/fail 표 → `내부테스트결과서/`
- [x] 판단 근거 요약(A0 반영)
- [x] 발견된 편차(A0 §3)

## §5. 프롬프트
> 작성 세션이 곧 실행 세션 — harness_04 절차 생략.

## §6. 다음 단계 예고
- 다음 단위: U4(피드백 리포트) 또는 U5(대시보드) — U2-c(화이트보드)는
  Could이므로 여유 시간에. `GEMINI_API_KEY` 확보 여부를 재확인.
