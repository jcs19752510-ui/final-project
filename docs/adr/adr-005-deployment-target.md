# ADR-005: 배포 인프라 (Kubernetes/GCP → 로컬/무료 PaaS)

- 날짜: 2026-09-07
- 상태: 제안됨 — AI가 기본값으로 자동 적용, 근거는 `자동진행/` 로그에 기록.
  사용자가 이견 있으면 언제든 반려 가능(harness_00 원칙 2 에스컬레이션).
- 결정권자: AI(작업지시서 기본값 적용) — 최종 확정은 사용자 확인 필요

## 배경 (Context)

원본 기획서 §7 Phase 7은 AWS/GCP VPC, EKS(Kubernetes) 클러스터, Blue/Green
배포, Prometheus/Grafana 모니터링을 전제합니다. 1인/4주/무예산 조건에서
클러스터 오케스트레이션 자체를 학습·구축하는 것은 프로젝트의 핵심 가치
(AI 모의면접 기능)와 무관한 시간 소모입니다.

## 검토한 대안 (Options)

| 대안 | 장점 | 단점 |
|---|---|---|
| A. 로컬 Docker Compose(FastAPI + PostgreSQL 단일 compose)로 실행·데모 | 완전 무료, 설정 단순, 발표/시연 시 노트북에서 바로 구동 가능 | 외부 URL로 공유 불가(발표 환경이 곧 서버가 됨) |
| B. Render.com / Fly.io 등 무료 티어 PaaS에 배포 | 외부 URL 공유 가능, 데모 링크 전달 용이 | 무료 티어는 유휴 시 슬립, 무료 DB가 일정 기간 후 만료되는 등 제약, 설정에 별도 시간 소요 |
| C. Kubernetes(EKS/GKE) 원안 그대로 | 원본 설계 보존, 확장성 시연 가능 | 1인/4주/무예산 조건에서 학습 곡선과 클라우드 비용 리스크가 매우 큼 |

## 결정 (Decision)

**A안(로컬 Docker Compose)을 기본으로 채택**하고, 시간이 남으면 **B안
(Render.com 등 무료 티어)을 Could-have로 추가**한다. Kubernetes/GCP
오케스트레이션(원안 C)은 MVP 범위에서 명시적으로 제외(Won't)한다.

## 결과/트레이드오프 (Consequences)

- 포기하는 것: 수평 확장(REQ-N-002), 500명 동시접속 부하테스트, Blue/Green
  무중단 배포. 1인 데모 규모에서는 필요하지 않다고 판단.
- `docker-compose.yml`은 서비스 1개(app) + DB 1개(postgres)로 구성하며,
  추후 Redis/Celery가 필요해지면(ADR-003 재검토 시) compose에 추가하는
  식으로 확장 가능하게 작성한다.
- 이 ADR은 상태를 "제안됨"으로 유지 — 사용자가 검토 후 "승인됨"으로 바꿔야
  하나, 작업지시서 §3 기본값 규칙에 따라 검토 대기 중에도 이 기본값으로
  먼저 진행한다(harness_00 원칙 2의 예외 조항).

## 관련 문서

- 관련 ADR: ADR-003(데이터 스택 — Redis/Celery 제거와 연동)
