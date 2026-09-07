"""aimock_u3a_trd.md §1: 샘플 질문 10문항(자체 작성, 실제 채용사 데이터 아님).

임베딩(vector)은 GEMINI_API_KEY 확보 전까지 비워둔다(§7 미결 항목) —
retrieve_candidates()는 category/difficulty 필터로만 동작한다.
"""

SAMPLE_QUESTIONS: list[dict] = [
    {"content": "자기소개를 부탁드립니다.", "category": "general", "difficulty": 1},
    {"content": "가장 자신있는 프로그래밍 언어와 그 이유를 설명해주세요.", "category": "general", "difficulty": 1},
    {"content": "MSA(마이크로서비스 아키텍처) 경험이 있다면 설명해주세요.", "category": "backend", "difficulty": 3},
    {"content": "REST API 설계 시 고려하는 원칙은 무엇인가요?", "category": "backend", "difficulty": 2},
    {"content": "데이터베이스 인덱스는 왜 필요하고 어떤 트레이드오프가 있나요?", "category": "backend", "difficulty": 3},
    {"content": "React의 상태 관리는 어떻게 하시나요?", "category": "frontend", "difficulty": 2},
    {"content": "브라우저 렌더링 성능을 개선한 경험이 있나요?", "category": "frontend", "difficulty": 3},
    {"content": "본인이 겪은 가장 어려운 기술적 문제와 해결 과정을 STAR 기법으로 설명해주세요.", "category": "behavioral", "difficulty": 3},
    {"content": "팀 내 의견 충돌을 해결한 경험이 있나요?", "category": "behavioral", "difficulty": 2},
    {"content": "시간 복잡도와 공간 복잡도의 트레이드오프를 예로 들어 설명해주세요.", "category": "algorithm", "difficulty": 2},
]
