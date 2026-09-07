# 단위 TRD — U1-b: 원본 미디어 암호화 저장 + 삭제 API

> `harness/harness_01_trd_template.md` 형식. 상위 문서:
> `docs/trd/aimock_master_trd.md` §3(N-003), §5(AC-M6), §7. 관련 ADR:
> `docs/adr/adr-004-media-capture-scope.md`.

## 문서 정보
- 프로젝트: aimock
- 단위(화면/기능) 이름: U1-b — 미디어 자산 업로드/암호화 저장/지원자 삭제 요청
- 작성일 / 버전: 2026-09-07 / v0.1
- 상태: 확정 (코드 착수)

## §0. 범위 및 흐름 개요
- 역할: 면접 턴에서 캡처된 원본 오디오/비디오 프레임을 암호화해 로컬
  디스크에 저장하고, 그 메타데이터를 `media_assets`로 관리한다. 지원자가
  삭제를 요청하면 파일과 레코드를 즉시 물리 삭제한다. U1의 계정 파기
  스케줄러가 실행될 때도 동일한 삭제 로직을 재사용한다.
- 이 단위는 U2-a/U3-a(면접 진행/AI 파이프라인)가 나중에 "업로드" 쪽을
  호출하게 될 하부 구조이므로, 지금은 **저장/삭제 API와 스키마만** 구현
  하고 실제 면접 흐름과의 연결은 U2-a에서 이어붙인다.
- 의존하는 다른 단위: U1(인증 — 업로드/삭제 모두 로그인 필요)
- 의존받는 단위: U2-a, U3-a, U1(탈퇴 파기 시 연쇄 삭제로 이 서비스 함수를
  호출)

## §0-1. 비기능 요구사항 체크
- 동시성: 동일 `media_asset` 삭제 요청이 중복으로 와도 두 번째는 404
  (이미 없음)로 idempotent하게 처리.
- 권한: 본인 소유(해당 interview의 candidate_id == 현재 사용자) 미디어만
  업로드/삭제 가능. 타인 소유 접근 시 403.
- 감사: 삭제 시각/사유(사용자 요청 vs 계정파기 연쇄)를 로그로만 남김
  (DB 테이블화는 MVP 범위 밖).
- 개인정보: 파일은 반드시 암호화 후 저장(`cryptography.Fernet`), DB에는
  평문 파일 내용이 절대 들어가지 않음(경로/메타데이터만).
- 삭제 정책: ADR-004 — 물리 삭제만 존재(소프트 삭제 없음). 삭제 시 파일
  시스템의 실제 파일도 함께 제거.

## §1. 데이터 구조
`MEDIA_ASSETS` 테이블(ADR-003 §ERD가 단일 진실 공급원): `id(uuid,pk)`,
`interview_id(fk)`, `turn_index`, `kind(audio/video_frame)`,
`storage_path`, `encrypted(bool)`, `created_at`.

> 참고: `interviews.candidate_id`로 소유권을 확인하므로, 이 단위 구현
> 시점에는 `interviews`/`users` 테이블이 이미 존재해야 한다(U1과 DB
> 스키마를 함께 마이그레이션).

## §2. 함수/API 명세

| 엔드포인트 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `POST /api/v1/interviews/{interview_id}/media` | Bearer, multipart(file, kind, turn_index) | `201 {id, kind, created_at}` / `403` / `404` | 원본 미디어 업로드+암호화 저장 |
| `DELETE /api/v1/media/{media_id}` | Bearer | `204` / `403` / `404` | 지원자 삭제 요청 |
| (내부) `purge_user_media(user_id)` | 스케줄러/탈퇴 로직에서 호출 | - | 사용자의 모든 media_assets 연쇄 삭제 |

## §3. 워크플로우 및 비즈니스 로직
- 업로드: `interview_id`로 interview를 조회 → `candidate_id`가 현재
  사용자와 다르면 403 → 파일을 `Fernet` 키(서버 환경변수
  `MEDIA_ENCRYPTION_KEY`)로 암호화 → `uploads/{interview_id}/{uuid}.enc`
  경로에 저장 → `media_assets` 레코드 생성.
- 삭제: `media_id`로 조회 → 연결된 interview의 `candidate_id`가 현재
  사용자와 다르면 403, 없으면 404 → 파일 삭제(`os.remove`) → DB 레코드
  삭제(hard delete) → 204.
- 계정 파기 연쇄: U1의 `purge_expired_users()`가 사용자를 지우기 전에
  `purge_user_media(user_id)`를 먼저 호출해 파일까지 정리(DB FK
  `ON DELETE CASCADE`만으로는 로컬 파일이 지워지지 않으므로 애플리케이션
  레벨에서 명시적으로 처리).

## §4. 상태/에러 코드

| 코드 | 의미 | 발생 조건 |
|---|---|---|
| 403 | 소유권 없음 | 다른 사용자의 interview/media에 접근 |
| 404 | 대상 없음 | 존재하지 않거나 이미 삭제된 media_id/interview_id |

## §5. 인수 조건 (Acceptance Criteria)
- [ ] AC-1: 오디오 파일을 업로드하면 201과 `media_asset` id를 받고, 실제
  디스크 파일은 평문이 아니라 암호화된 바이트로 저장된다(원본 바이트와
  다름을 확인).
- [ ] AC-2: 생성된 `media_id`로 DELETE 요청하면 204를 반환하고, 디스크의
  파일이 실제로 사라지며 DB 조회 시 해당 레코드가 없다.
- [ ] AC-3: 이미 삭제된 `media_id`를 다시 DELETE하면 404를 반환한다.
- [ ] AC-4: 다른 사용자의 interview에 속한 media를 삭제 시도하면 403을
  반환한다.
- [ ] AC-5: `purge_user_media(user_id)` 호출 시 해당 사용자 소유 interview
  전체의 media_assets 파일과 레코드가 모두 삭제된다.

## §6. 테스트 시나리오

| 시나리오 | 입력/조건 | 기대 결과 | 대응 AC |
|---|---|---|---|
| 정상 업로드 | 오디오 바이트 업로드 | 201, 파일 암호화 확인 | AC-1 |
| 정상 삭제 | 방금 만든 media_id | 204, 파일/레코드 소멸 | AC-2 |
| 중복 삭제 | 이미 삭제된 media_id | 404 | AC-3 |
| 타인 소유 | 다른 후보자의 media_id | 403 | AC-4 |
| 연쇄 삭제 | purge_user_media 호출 | 해당 사용자 전체 media 소멸 | AC-5 |

## §7. 미결 항목
| 항목 | 권장 기본값 | 확정 필요 여부 |
|---|---|---|
| 업로드 파일 최대 용량 | 오디오 20MB, 프레임 이미지 5MB | 아니오(기본값 적용) |
| 암호화 키 보관 방식 | 환경변수(`MEDIA_ENCRYPTION_KEY`), 실서비스 전환 시 KMS로 교체 검토 | 아니오(MVP 기본값) |
