# HARNESS_BASIC

AI(Claude Code 등)에게 개발을 위임할 때, "무엇을 사람이 결정하고 무엇을
AI가 실행할지"의 경계선을 문서와 절차로 미리 고정해 둔 **범용 거버넌스
프레임워크**입니다. 특정 업무 프로그램(예: 재고관리, 예약시스템, 인사관리
등)의 구현체가 아니라, 그런 프로그램들을 만들 때 공통으로 가져다 쓰는
**기본 시스템(하네스)** 그 자체입니다.

## 무엇부터 읽어야 하나

| 목적 | 문서 |
|---|---|
| 5분 안에 전체 그림 파악 | [`harness/harness_00_definition.md`](harness/harness_00_definition.md) |
| 전체 구조를 다이어그램으로 | [`harness/harness_structure_diagram.md`](harness/harness_structure_diagram.md) |
| Claude Code 세션 지침(원칙/규칙) | [`CLAUDE.md`](CLAUDE.md) |
| SOP 및 타협 불가 8원칙 | [`harness/harness_00_overview.md`](harness/harness_00_overview.md) |
| 문서 21종 전체 목록 | `harness/harness_00_definition.md` §3 |

## 이 저장소를 실제 프로젝트에 연결하는 방법

**이 저장소(`HARNESS_BASIC`) 자체에는 실제 프로젝트의 코드/TRD/문서를
절대 커밋하지 않습니다.** `docs/`, `src/`, `tests/`는 항상 빈 골격
(`.gitkeep`)만 유지합니다.

새 프로젝트를 시작할 때는 아래 순서를 따르세요.

1. 이 저장소의 GitHub Settings → General → **Template repository** 체크
   (사람이 직접 — 최초 1회만 하면 됨)
2. 새 프로젝트마다 이 저장소 페이지의 **"Use this template"** 버튼으로
   새 저장소 생성 (harness 전체가 그대로 복사되어 시작)
3. 새 저장소의 `CLAUDE.md` "프로젝트 개요"를 실제 프로젝트 설명으로
   교체 (하네스 원칙 8개와 Git 작업 관련 규칙은 그대로 유지)
4. `harness/harness_00_definition.md` §4의 Phase A부터 순서대로 진행

이 방식(A안)을 선택한 이유와 대안(수동 복사/submodule)은
[`CLAUDE.md`](CLAUDE.md) "저장소 연결 방식" 섹션에 동일하게 설명돼
있습니다.

## 라이선스

[MIT](LICENSE)
