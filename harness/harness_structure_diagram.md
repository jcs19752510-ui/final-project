# 하네스 시스템 전체 구조도

> 이 문서는 `harness/` 21종 문서의 전체 구조를 한눈에 보기 위한 시각 자료입니다.
> 각 문서의 상세 내용은 해당 `harness_NN_*.md` 파일을, "왜 필요한가"는
> 루트 `CLAUDE.md` "확장 문서" 섹션을 참조하세요. 이 저장소는 도메인
> 중립이므로, 아래 다이어그램도 특정 업무 프로그램과 무관한 범용 구조입니다.

---

## 1. 전체 레이어 구조 (문서 21종 배치)

프로젝트 생애주기를 "거버넌스 백본 + 5개 레이어"로 나눠 문서를 배치합니다.
화살표는 레이어 간 진행 순서, 점선은 회고 루프를 뜻합니다.

```mermaid
flowchart TD
    subgraph BB["⚖️ 거버넌스 백본 (전 레이어 관통)"]
        B1["00_definition<br/>전체 지도(5분 요약)"]
        B2["00_overview<br/>SOP·타협불가 8원칙"]
        B3["05_execution_infra<br/>브랜치·CI·권한·에스컬레이션"]
    end

    subgraph L1["🎯 기획 — 무엇을, 언제 만들 것인가"]
        F1["07_release_planning<br/>MoSCoW·MVP·릴리스 우선순위"]
        F2["11_raci<br/>역할과 책임"]
        F3["12_change_management<br/>변경관리 프로세스"]
    end

    subgraph L2["🏗️ 설계 — 어떻게 만들 것인가"]
        D1["08_adr<br/>아키텍처 결정 기록"]
        D2["13_tech_conventions<br/>전역 기술 컨벤션"]
        D3["10_data_lifecycle<br/>개인정보 생애주기 정책"]
    end

    subgraph L3["⚙️ 실행 — AI에게 위임하고 검증"]
        E1["01_trd_template<br/>무엇을 만드는가+AC"]
        E2["02_work_order_template<br/>이번 세션 경계"]
        E3["04_prompt_generator<br/>최종 프롬프트 조합"]
        E4["03_handoff_template(A0)<br/>인수인계"]
        E5["14_test_data_management<br/>마스킹 시드 관리"]
        E6["15_parallel_work<br/>병렬 작업·인터페이스 계약"]
    end

    subgraph L4["🚀 운영 — 세상에 내놓고 지키기"]
        O1["09_deployment_runbook<br/>배포·롤백 절차"]
        O4["20_backup_dr<br/>백업·재해복구(DR)"]
        O2["17_monitoring<br/>모니터링·알림"]
        O3["16_tech_debt_log<br/>기술부채 로그"]
    end

    subgraph L5["🔄 메타 — 하네스 자체를 진화시키기"]
        M1["06_meta_improvement<br/>회고·실패패턴 라이브러리"]
        M2["18_cost_tracking<br/>AI 세션 비용·시간 추적"]
        M3["19_template_validation<br/>템플릿 필수필드 검증"]
    end

    BB --> L1 --> L2 --> L3 --> L4 --> L5
    M1 -. "다음 프로젝트 착수 시<br/>실패패턴 선반영" .-> L1

    classDef backbone fill:#374151,color:#fff,stroke:#1f2937
    classDef plan fill:#1d4ed8,color:#fff,stroke:#1e3a8a
    classDef design fill:#7c3aed,color:#fff,stroke:#5b21b6
    classDef exec fill:#0f766e,color:#fff,stroke:#115e59
    classDef ops fill:#b45309,color:#fff,stroke:#92400e
    classDef meta fill:#be185d,color:#fff,stroke:#9d174d
    class B1,B2,B3 backbone
    class F1,F2,F3 plan
    class D1,D2,D3 design
    class E1,E2,E3,E4,E5,E6 exec
    class O1,O2,O3,O4 ops
    class M1,M2,M3 meta
```

---

## 2. 표준 실행 절차 (SOP) — Phase A → B → C

Phase A는 프로젝트당 1회, Phase B는 실행 단위 수만큼 반복, Phase C는 마감 시 1회입니다.

```mermaid
flowchart TD
    Start(["프로젝트 착수"]) --> A1["Phase A-1<br/>요구사항 + 비기능요구사항 정의<br/>(동시성·권한·감사·개인정보)"]
    A1 --> A2["Phase A-2<br/>데이터 모델(ERD) 확정<br/>→ 08_adr에 근거 기록"]
    A2 --> A3["Phase A-3<br/>전역 기술 컨벤션 확정<br/>→ 13_tech_conventions"]
    A3 --> A4["Phase A-4<br/>마스터 TRD 작성"]
    A4 --> A5["Phase A-5<br/>릴리스 우선순위 확정<br/>→ 07_release_planning(MoSCoW)"]
    A5 --> A6["Phase A-6<br/>위험도+가치 기준<br/>실행 단위 순서 확정"]

    A6 --> Loop{{"Phase B<br/>단위별 실행 루프<br/>(단위 수만큼 반복)"}}
    Loop --> B1["B-1 단위 TRD 세부 스펙<br/>01_trd_template"]
    B1 --> B2["B-2 AC/테스트케이스 확정<br/>(코드 작성 전 필수)"]
    B2 --> B3["B-3 작업지시서 작성<br/>02_work_order_template"]
    B3 --> B4["B-4 프롬프트 생성<br/>04_prompt_generator → AI 위임"]
    B4 --> B5["B-5 AI 실행<br/>(계획→코드→테스트→디버깅, AI 자율 루프)"]
    B5 --> B6{"B-6 사람 검증<br/>AC pass/fail + diff 리뷰"}
    B6 -- Fail --> B4
    B6 -- Pass --> B7["B-7 버전관리 반영<br/>(사람이 직접 확인 후 진행)"]
    B7 --> B8["B-8 A0 인수인계 갱신<br/>03_handoff_template"]
    B8 --> Loop

    Loop -- "전체 단위 완료" --> C1["Phase C-1<br/>단위 간 연결 E2E 테스트"]
    C1 --> C2["Phase C-2<br/>배포 실행<br/>09_deployment_runbook"]
    C2 --> C3["Phase C-3<br/>운영 모니터링 구성<br/>17_monitoring"]
    C3 --> C4["Phase C-4<br/>프로젝트 회고 + 하네스 버전업<br/>06_meta_improvement"]
    C4 -.->|"다음 프로젝트에 학습 반영"| Start
```

---

## 3. 문서 간 데이터 흐름 — 누가 누구에게 무엇을 넘기는가

Phase B(단위별 실행 루프) 안에서 문서가 실제로 어떻게 서로 입력/출력이 되는지를
보여줍니다. "사람 작성"과 "AI 초안"을 구분해 어디서 검증 게이트가 걸리는지 표시합니다.

```mermaid
flowchart LR
    REQ["요구사항 정의서<br/>(사람 작성)"] --> ADR["08_adr<br/>(사람 승인)"]
    REQ --> TRD0["A0 데이터모델 TRD<br/>(사람 확정)"]
    TRD0 --> MTRD["마스터 TRD<br/>(사람 작성)"]
    ADR --> MTRD
    TC["13_tech_conventions<br/>(사람 확정)"] --> MTRD
    MTRD --> UTRD["단위 TRD + AC<br/>(AI 초안 → 사람 확정)"]
    UTRD --> WO["작업지시서<br/>(사람 작성)"]
    WO --> PROMPT["04 프롬프트 생성<br/>(사람+AI 조합)"]
    PROMPT --> AI(["AI 실행<br/>(코드/테스트)"])
    AI --> REVIEW{"사람 diff 리뷰<br/>+ AC 판정"}
    REVIEW -- "Fail: 재작업" --> PROMPT
    REVIEW -- Pass --> A0["A0 인수인계<br/>(AI 초안 → 사람 검증)"]
    A0 -->|"편차 발견 시"| FAIL["06 실패패턴 라이브러리<br/>(일반화하여 등록)"]
    FAIL -.->|"다음 단위 착수 전 재확인"| UTRD
    A0 --> NEXT["다음 단위 TRD"]

    classDef human fill:#1e7d34,color:#fff,stroke:#145a24
    classDef ai fill:#2563eb,color:#fff,stroke:#1e3a8a
    classDef gate fill:#b91c1c,color:#fff,stroke:#7f1d1d
    class REQ,TRD0,MTRD,TC,WO human
    class AI,PROMPT ai
    class REVIEW gate
```

---

## 4. 되돌리기 어려운 결정 — 사람 승인 게이트가 걸리는 지점

하네스 전체에서 "AI가 혼자 확정할 수 없고 후보안만 내야 하는" 지점만 따로 모았습니다.

```mermaid
flowchart TD
    T1["데이터 모델 변경<br/>(테이블/컬럼 추가·삭제)"] --> GATE{"🔒 사람 승인 게이트<br/>(CLAUDE.md 원칙 8)"}
    T2["삭제 정책<br/>(물리삭제 vs 소프트삭제)"] --> GATE
    T3["권한 구조<br/>(역할/접근범위)"] --> GATE
    T4["개인정보 보유·마스킹 정책<br/>(10_data_lifecycle)"] --> GATE
    GATE -->|"AI는 후보 A/B/C만 제시"| CANDIDATES["후보안 문서화<br/>(장단점 비교)"]
    CANDIDATES --> HUMAN["사람이 선택/승인"]
    HUMAN --> RECORD["08_adr에 결정 기록<br/>(배경/대안/결정/트레이드오프)"]
```

---

## 5. 문서 목차 요약표

| 코드 | 이름 | 레이어 | 우선순위 |
|---|---|---|---|
| `00_definition` | 하네스 정의(전체 지도) | 백본 | 기본 |
| `00_overview` | SOP·원칙 | 백본 | 기본 |
| `05_execution_infra` | 실행 인프라(브랜치/CI/권한) | 백본 | 기본 |
| `01_trd_template` | TRD 템플릿 | 실행 | 기본 |
| `02_work_order_template` | 작업지시서 | 실행 | 기본 |
| `03_handoff_template` | A0 인수인계 | 실행 | 기본 |
| `04_prompt_generator` | 프롬프트 생성기 | 실행 | 기본 |
| `06_meta_improvement` | 회고·실패패턴 | 메타 | 기본 |
| `07_release_planning` | 릴리스·우선순위 계획 | 기획 | 🔴 Critical |
| `08_adr` | ADR | 설계 | 🔴 Critical |
| `09_deployment_runbook` | 배포·롤백 절차 | 운영 | 🔴 Critical |
| `10_data_lifecycle` | 개인정보 생애주기 | 설계 | 🔴 Critical |
| `11_raci` | RACI | 기획 | 🟡 Important |
| `12_change_management` | 변경관리 | 기획 | 🟡 Important |
| `13_tech_conventions` | 전역 기술 컨벤션 | 설계 | 🟡 Important |
| `14_test_data_management` | 테스트 데이터 관리 | 실행 | 🟡 Important |
| `15_parallel_work` | 병렬 작업 관리 | 실행 | 🟡 Important |
| `16_tech_debt_log` | 기술부채 로그 | 운영 | 🟢 Nice |
| `17_monitoring` | 모니터링·알림 | 운영 | 🟢 Nice |
| `18_cost_tracking` | 비용·시간 추적 | 메타 | 🟢 Nice |
| `19_template_validation` | 템플릿 검증 체크 | 메타 | 🟢 Nice |
| `20_backup_dr` | 백업·재해복구 정책 | 운영 | 🔴 Critical |

**최소 시작 경로**: 급하고 작은 프로젝트라면 `00_overview → 01 → 02 → 05` 네 개만
읽고 시작해도 됩니다. 나머지는 위 §1 지도 순서대로 필요할 때 끌어다 쓰면 됩니다.
1인 프로젝트에서 어떤 문서를 생략해도 되는지는 `19_template_validation.md` §4를
참고하세요.
