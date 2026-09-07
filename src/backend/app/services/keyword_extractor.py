"""docs/trd/aimock_u4_trd.md §3. LLM 불필요 — 로컬 빈도 분석(형태소 분석기 미사용, MVP §7 미결)."""

import re
from collections import Counter

_STOPWORDS = {
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "의",
    "도",
    "와",
    "과",
    "그",
    "저",
    "제",
    "합니다",
    "했습니다",
    "있습니다",
    "입니다",
}

_TOKEN_PATTERN = re.compile(r"[가-힣A-Za-z0-9]+")


def extract(texts: list[str], top_n: int = 5) -> list[str]:
    tokens: list[str] = []
    for text in texts:
        for token in _TOKEN_PATTERN.findall(text):
            if len(token) < 2 or token in _STOPWORDS:
                continue
            tokens.append(token)

    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_n)]
