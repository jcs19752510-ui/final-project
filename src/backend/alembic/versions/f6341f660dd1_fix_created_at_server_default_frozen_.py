"""fix created_at server_default frozen literal bug

2026-09-08 실제 발견: `server_default="now()"`를 SQLAlchemy Column에 순수
Python 문자열로 주면, 초기 마이그레이션(68f6341f989a) 적용 시 DDL에
`now()` 함수 호출이 아니라 **그 적용 시점의 고정 리터럴 타임스탬프**로
굳어버리는 것이 확인됨 — `users`/`media_assets`/`coding_submissions`/
`evaluation_reports`/`whiteboard_snapshots` 5개 테이블의 `created_at`이
전부 최초 `alembic upgrade head` 실행 시각
(2026-09-07 12:30:31.422073+00) 그대로 고정되어 있었음(방금 새로 만든
계정/미디어까지 전부 같은 값으로 찍히는 것을 실제 DB 조회로 확인,
`내부테스트결과서/` 참조). `transcripts.created_at`은 이미 Python 쪽
`datetime.now(timezone.utc)` 콜러블 기본값을 써서 이 문제가 없었음
(같은 문제를 대화 순서 정렬 버그로 먼저 발견해 고쳤던 이력, 모델 주석
참조) — 이번에 나머지 5개 테이블에도 동일 원인이 있었음을 추가로 발견.

이 마이그레이션은 이미 저장된 행의 `created_at` 값은 건드리지 않고(과거
데이터를 임의로 재작성하는 것은 별도 판단 필요 — 하네스 원칙: 되돌리기
어려운 결정 금지), 컬럼의 DEFAULT 절만 실제 `now()` 함수 호출로 바로잡아
**이후 생성되는 행부터** 정확한 시각이 기록되도록 한다.

Revision ID: f6341f660dd1
Revises: 68f6341f989a
Create Date: 2026-09-08 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6341f660dd1'
down_revision: Union[str, None] = '68f6341f989a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_AFFECTED_TABLES = [
    "users",
    "media_assets",
    "coding_submissions",
    "evaluation_reports",
    "whiteboard_snapshots",
]


def upgrade() -> None:
    for table in _AFFECTED_TABLES:
        op.alter_column(
            table,
            "created_at",
            server_default=sa.text("now()"),
        )


def downgrade() -> None:
    # 원래(버그가 있던) 고정 리터럴로는 되돌리지 않는다 — 그 리터럴 값 자체가
    # 버그의 산물이라 의미가 없음. 대신 DEFAULT 절을 제거해 애플리케이션이
    # 명시적으로 값을 넣지 않으면 NULL이 되던 이전 상태와 유사하게 되돌림
    # (컬럼 자체는 nullable=False라 실제로는 항상 애플리케이션/삽입 시 값이
    # 필요해짐 — 다운그레이드는 스키마 원복 목적일 뿐 운영상 사용 비권장).
    for table in _AFFECTED_TABLES:
        op.alter_column(
            table,
            "created_at",
            server_default=None,
        )
