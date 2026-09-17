from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007_create_escalation_events"
down_revision: Union[str, None] = "006_create_escalation_flags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    op.create_table(
        "escalation_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("hair_assessments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("flag_code", sa.String(), nullable=False),
        sa.Column("trigger_reason", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_escalation_events_user_id", "escalation_events", ["user_id"])
    op.create_index("ix_escalation_events_assessment_id", "escalation_events", ["assessment_id"])
    op.create_index("ix_escalation_events_flag_code", "escalation_events", ["flag_code"])


def downgrade() -> None:
    op.drop_index("ix_escalation_events_flag_code", table_name="escalation_events")
    op.drop_index("ix_escalation_events_assessment_id", table_name="escalation_events")
    op.drop_index("ix_escalation_events_user_id", table_name="escalation_events")
    op.drop_table("escalation_events")
