"""aimock_u3a_trd.md §1: 샘플 질문 10문항(자체 작성, 실제 채용사 데이터 아님).

임베딩(vector)은 GEMINI_API_KEY 확보 전까지 비워둔다(§7 미결 항목) —
retrieve_candidates()는 category/difficulty 필터로만 동작한다.

2026-09-18: `rubric_json`을 실제 채점 기준으로 채움(그동안 전부 빈 dict라
컬럼은 있는데 아무도 안 읽는 "죽은 컬럼" 상태였던 것을 해소 — 계획서
원문 REQ-F-007 "사전에 정의된 루브릭에 따라 각 역량별 점수를 산출"에
맞춤). 각 항목은 "이 질문에 대한 좋은 답변이 반드시 짚어야 할 요소"를
1~3개의 체크리스트 형태로 담고, `app/ai/llm.py`의
`_build_user_message`가 이 내용을 LLM 프롬프트에 실어 보내
`evaluation.rubric_match`(달성 여부)를 채우는 데 쓴다. 채점 배점표가
아니라 "무엇을 확인해야 하는가"이므로 값은 전부 자유서술 문자열이다.
"""

SAMPLE_QUESTIONS: list[dict] = [
    {
        "content": "자기소개를 부탁드립니다.",
        "category": "general",
        "difficulty": 1,
        "rubric_json": {
            "핵심 경력 요약": "직무와 관련된 경력/역할을 구체적으로 언급하는가",
            "논리적 구성": "두괄식으로 핵심부터 전달하는가",
        },
    },
    {
        "content": "가장 자신있는 프로그래밍 언어와 그 이유를 설명해주세요.",
        "category": "general",
        "difficulty": 1,
        "rubric_json": {
            "구체적 근거": "언어의 특징을 실제 사용 경험과 연결해 설명하는가",
            "트레이드오프 인식": "그 언어의 한계나 다른 언어와의 차이도 언급하는가",
        },
    },
    {
        "content": "MSA(마이크로서비스 아키텍처) 경험이 있다면 설명해주세요.",
        "category": "backend",
        "difficulty": 3,
        "rubric_json": {
            "서비스 분리 기준": "도메인/책임 기준으로 서비스를 나눈 근거를 설명하는가",
            "트랜잭션 관리": "분산 트랜잭션·데이터 정합성 문제를 어떻게 다뤘는지 언급하는가",
            "실무 사례": "실제 겪은 문제와 해결 과정을 구체적으로 제시하는가",
        },
    },
    {
        "content": "REST API 설계 시 고려하는 원칙은 무엇인가요?",
        "category": "backend",
        "difficulty": 2,
        "rubric_json": {
            "리소스 중심 설계": "URI/메서드를 리소스와 행위로 구분해 설계하는가",
            "상태 코드/에러 처리": "적절한 HTTP 상태 코드와 일관된 에러 응답을 언급하는가",
        },
    },
    {
        "content": "데이터베이스 인덱스는 왜 필요하고 어떤 트레이드오프가 있나요?",
        "category": "backend",
        "difficulty": 3,
        "rubric_json": {
            "조회 성능 원리": "인덱스가 조회 속도를 높이는 원리(B-Tree 등)를 이해하고 있는가",
            "쓰기 비용 트레이드오프": "인덱스가 늘어나면 INSERT/UPDATE가 느려지는 이유를 설명하는가",
        },
    },
    {
        "content": "React의 상태 관리는 어떻게 하시나요?",
        "category": "frontend",
        "difficulty": 2,
        "rubric_json": {
            "로컬 vs 전역 구분": "컴포넌트 로컬 상태와 전역 상태를 구분해 설명하는가",
            "도구 선택 근거": "선택한 상태관리 도구(Context/Redux/Zustand 등)를 고른 이유를 설명하는가",
        },
    },
    {
        "content": "브라우저 렌더링 성능을 개선한 경험이 있나요?",
        "category": "frontend",
        "difficulty": 3,
        "rubric_json": {
            "병목 진단 방법": "프로파일링 등으로 병목을 실제로 측정했는지 언급하는가",
            "구체적 개선 기법": "메모이제이션/가상화/코드스플리팅 등 구체적 기법을 제시하는가",
        },
    },
    {
        "content": "본인이 겪은 가장 어려운 기술적 문제와 해결 과정을 STAR 기법으로 설명해주세요.",
        "category": "behavioral",
        "difficulty": 3,
        "rubric_json": {
            "Situation/Task 명확성": "상황과 본인의 역할/과제를 구체적으로 설명하는가",
            "Action의 구체성": "본인이 실제로 취한 행동을 두루뭉술하지 않게 설명하는가",
            "Result 정량화": "결과를 가능하면 수치나 명확한 변화로 제시하는가",
        },
    },
    {
        "content": "팀 내 의견 충돌을 해결한 경험이 있나요?",
        "category": "behavioral",
        "difficulty": 2,
        "rubric_json": {
            "상대 관점 이해": "갈등 상대의 입장을 이해하려는 시도를 언급하는가",
            "건설적 해결 과정": "감정적 대응이 아닌 절차/합의 기반으로 해결했는가",
        },
    },
    {
        "content": "시간 복잡도와 공간 복잡도의 트레이드오프를 예로 들어 설명해주세요.",
        "category": "algorithm",
        "difficulty": 2,
        "rubric_json": {
            "구체적 예시": "실제 알고리즘/자료구조 예시로 트레이드오프를 설명하는가",
            "상황별 선택 기준": "언제 시간을, 언제 공간을 우선해야 하는지 기준을 제시하는가",
        },
    },
]
