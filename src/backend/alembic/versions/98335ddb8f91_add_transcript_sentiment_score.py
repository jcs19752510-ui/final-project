"""add transcripts.sentiment_score

2026-09-18: 원본 계획서 ERD(§6.1 Transcripts: ..., sentiment_score)에 있던
필드인데, 실제 구현 시 누락돼 있던 것을 사용자와의 아키텍처 검토 과정에서
발견. ADR로 제외 결정된 적이 없는, 단순 구현 누락이라 이번에 추가한다.

speaker="user" 턴에만 LLM 평가(app/ai/llm.py의 evaluation.sentiment_score,
1~5 척도, 기존 technical_accuracy와 동일 척도로 통일)로 채워지고, ai 발화나
LLM이 evaluation을 안 준 경우는 계속 NULL로 남는다 — 그래서 NOT NULL 제약을
걸지 않는다.

Revision ID: 98335ddb8f91
Revises: a1c3e7f2b904
Create Date: 2026-09-18 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '98335ddb8f91'
down_revision: Union[str, None] = 'a1c3e7f2b904'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transcripts",
        sa.Column("sentiment_score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transcripts", "sentiment_score")
