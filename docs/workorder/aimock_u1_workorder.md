# 작업지시서 — U1(인증/탈퇴) + U1-b(미디어 저장/삭제)

> `harness/harness_02_work_order_template.md` 형식. U1과 U1-b를 한 세션에
> 묶은 이유: 둘 다 `users`/`interviews` 스키마 경계를 공유하고, U1-b가
> 단독으로는 3개 미만 AC라 문서 오버헤드가 작업량보다 커지는 것을 피하기
> 위함(harness_00_overview §7 "너무 작다는 신호" 회피).

## 문서 정보
- 프로젝트/단위: aimock / U1 + U1-b
- 참조 TRD: `docs/trd/aimock_u1_trd.md`, `docs/trd/aimock_u1b_trd.md`
- 작성일: 2026-09-07

## §0. 전제 조건
- 완료되어 있어야 하는 것: Phase A 전체(ADR-001~006, 마스터 TRD, 릴리스
  계획, 기술컨벤션) — 완료됨.
- 참고 자료: `docs/adr/adr-003-data-stack.md`(ERD 단일 진실 공급원),
  `docs/tech_conventions.md`(폴더구조/네이밍/에러포맷).

## §1. 이번 단계 범위
- [x] 리포지토리 스켈레톤(`src/backend/`) 및 `docker-compose.yml`(Postgres+pgvector) 작성
- [x] SQLAlchemy 모델 전체(ADR-003 ERD 8개 테이블) 작성 — 스키마는 지금
  전부 만들고, 이후 단위(U2~U5)는 비즈니스 로직만 추가
- [x] Alembic 마이그레이션 초기 리비전 작성
- [x] U1: signup/login/me/withdraw API + JWT + 탈퇴 자동복구 로직
- [x] U1: `purge_expired_users` 스케줄러(APScheduler)
- [x] U1-b: 미디어 업로드(암호화)/삭제 API + `purge_user_media`
- [x] pytest 테스트(TRD §6 전체) 작성 및 실제 Postgres 컨테이너로 실행,
  AC pass/fail 확인

## §2. 안 하는 것 (Out of Scope)
- 프론트엔드(React) 화면 — 이번 단위는 백엔드 API까지만.
- U2(면접 진행)/U3(AI 파이프라인) 비즈니스 로직 — 테이블만 존재, 라우터는
  다음 단위에서.
- 이메일 인증/비밀번호 재설정 메일 발송 — MVP 범위 밖(Won't, 마스터 TRD에
  없는 항목이므로 임의 추가 금지).
- 실제 Gemini/faster-whisper 연동 — U3-a에서.

## §3. 착수 전 확정 정책 (TRD §7 기반)
| 미결 항목 | 권장 기본값 | 이번 세션 적용 여부 |
|---|---|---|
| 비밀번호 최소 길이 | 8자 이상 | 적용 |
| JWT 만료시간 | 24시간 | 적용 |
| 업로드 파일 최대 용량 | 오디오 20MB, 이미지 5MB | 적용 |
| 암호화 키 보관 | 환경변수 `MEDIA_ENCRYPTION_KEY` | 적용 |

## §4. 완료 후 받을 결과물
- [x] 소스 코드 (경로: `src/backend/`)
- [x] 실행/테스트 결과 로그 (본 세션 응답에 pytest 출력 포함)
- [x] AC 대비 pass/fail 표 (아래 실행 후 A0 문서에 반영)
- [x] 판단 근거 요약
- [x] 발견된 TRD와의 편차 (있다면 A0에 기록)

## §5. 프롬프트
> 이번 세션은 작업지시서를 작성한 동일 세션(Claude Code)이 그대로
> 실행하므로 별도 프롬프트 생성/전달 절차(harness_04)를 생략함 — 위
> §1~§3을 그대로 실행 지침으로 사용.

## §6. 다음 단계 예고
- 다음 단위: U2-a(턴 기반 질문-답변) — U1에서 만든 인증을 그대로 사용.
- 착수 전 확인: U1-b의 media 업로드 API가 실제 면접 흐름(턴 종료 시
  자동 호출)과 어떻게 이어질지 U2-a TRD에서 다시 명세.
