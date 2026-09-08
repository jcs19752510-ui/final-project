"""add report generation status tracking (async report generation)

2026-09-08: 운영 환경(Render)에서 사용자가 "피드백 리포트 생성이 1분 이상
걸린다"를 실제로 보고 — 원인은 `report_service.generate_report()`가 HTTP
요청 한 번 안에서 LLM 호출 + 턴마다 저장된 video_frame 전부를 DeepFace로,
audio 전부를 librosa로 순차 분석하던 것(마스터 TRD 원래 아키텍처 다이어그램
에는 "표정/음성운율 분석은 BackgroundTasks로 비동기 처리"라고 이미 명시돼
있었으나 실제 구현 시 누락됐던 것 — 원본 우선 원칙으로 재확인 후 발견).

이 마이그레이션은 리포트 생성을 실제로 백그라운드로 넘기기 위해 진행
상태를 추적할 컬럼 3개를 `evaluation_reports`에 추가한다:
- `status`(NOT NULL): "processing"/"completed"/"failed" — 서비스 계층에서만
  값을 만들어 넣음(다른 status류 컬럼과 동일하게 애플리케이션 레벨 검증,
  DB CHECK 제약 없음 — 전역 기술 컨벤션과 일치).
- `error_message`(nullable): 생성 실패 시 사용자에게 보여줄 안전한 메시지
  (내부 스택트레이스/시크릿 없음 — `report_service`가 항상 정제된 문구만
  넣음).
- `processing_started_at`(nullable): "processing" 진입 시각. 서버 재시작
  등으로 백그라운드 작업이 중간에 죽어 영원히 "생성 중"에 멈추는 것을
  막기 위해, 이 시각이 `report_service.PROCESSING_STALE_AFTER`(5분)보다
  오래됐으면 재시도를 허용한다(aimock_u4_trd.md §3-1 참조).

기존에 이미 생성된 리포트 행(전부 실제 점수가 채워진 완료 상태)은
`status='completed'`로 백필한다 — 하네스 원칙(되돌리기 어려운 결정 금지)
에 따라 과거 데이터의 다른 컬럼 값은 건드리지 않는다.

Revision ID: a1c3e7f2b904
Revises: f6341f660dd1
Create Date: 2026-09-08 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1c3e7f2b904'
down_revision: Union[str, None] = 'f6341f660dd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_reports",
        sa.Column("status", sa.String(), nullable=False, server_default="completed"),
    )
    # 백필 전용 기본값이었을 뿐, 앞으로는 애플리케이션이 항상 명시적으로
    # 값을 넣어야 한다(다른 status류 흐름과 동일한 원칙) — 백필 후 제거.
    op.alter_column("evaluation_reports", "status", server_default=None)

    op.add_column(
        "evaluation_reports",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "evaluation_reports",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluation_reports", "processing_started_at")
    op.drop_column("evaluation_reports", "error_message")
    op.drop_column("evaluation_reports", "status")
