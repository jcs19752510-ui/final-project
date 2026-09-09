# 웹 AI 모의면접 플랫폼 (MVP)

지원자가 웹 브라우저에서 AI 면접관과 턴 기반(녹음 버튼) 모의면접을 진행하고,
답변 내용·기술 코딩 테스트·비언어적 지표(표정/음성 운율)를 종합한 피드백
리포트와 채용 적합도 점수를 받는 1인 개발 파이널 프로젝트입니다.
   
- **원본 기획서**: [`00 파이널 프로젝트 계획서/`](00%20파이널%20프로젝트%20계획서/) —
  엔터프라이즈 프로덕션급 스펙(Kubernetes/Oracle/Pinecone/Hume AI/GCP 등)
- **실제 MVP 아키텍처와 축소 근거**: [`docs/adr/adr-001-mvp-architecture.md`](docs/adr/adr-001-mvp-architecture.md)
- **개발 제약**: 1인, 4주 이내, Claude Code 구독료 외 전부 무료 스택

이 저장소는 원래 프로젝트 무관 범용 거버넌스 하네스 골격(`HARNESS_BASIC`)
이었으나, 2026-09-07 사용자 결정으로 이 파이널 프로젝트 자체의 저장소로
전환되었습니다. `harness/` 폴더(21종 프로세스 가이드 문서)는 원래 목적대로
도메인 중립을 유지하며 수정하지 않고, 이 프로젝트의 실제 산출물은 전부
`docs/`(TRD/ADR/작업지시서/인수인계)·`src/`·`tests/`에 쌓습니다.

## 무엇부터 읽어야 하나

| 목적 | 문서 |
|---|---|
| 프로젝트 작업 이력(무엇을 왜 결정했는지) | [`CLAUDE.md`](CLAUDE.md) |
| 아키텍처 결정 기록(ADR) | [`docs/adr/`](docs/adr/) |
| 마스터 TRD / 요구사항 | [`docs/trd/`](docs/trd/) |
| 하네스(프로세스 가이드) 5분 요약 | [`harness/harness_00_definition.md`](harness/harness_00_definition.md) |
| 하네스 SOP 및 타협 불가 8원칙 | [`harness/harness_00_overview.md`](harness/harness_00_overview.md) |
| 사람이 컨펌 없이 자동진행을 지시한 결정 로그 | [`자동진행/`](자동진행/) |

## 하네스 프레임워크를 다른 프로젝트에 다시 쓰려면

이 저장소는 이제 특정 프로젝트 저장소로 전환되었으므로, 범용 골격이
필요하면 이 저장소를 그대로 복사하지 말고 전환 이전 커밋(또는 별도로
유지되는 `HARNESS_BASIC` 원본)에서 GitHub **Template repository** 기능으로
새 저장소를 만드세요. 상세 절차와 대안 검토는 [`CLAUDE.md`](CLAUDE.md)
"저장소 전환 결정" 섹션에 설명돼 있습니다.

## 라이선스

[MIT](LICENSE)
