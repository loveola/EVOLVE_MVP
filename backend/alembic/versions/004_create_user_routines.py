"""create user_routines table
Revision ID: 004_create_user_routines
Revises: 003_seed_rules_config
Create Date: 2026-09-09 23:10:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "004_create_user_routines"
down_revision: Union[str, None] = "003_seed_rules_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    op.create_table(
        "user_routines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("hair_assessments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("active_problems", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),

        sa.Column("cause_explanation_keys", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("protocols", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("roadmap", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("product_weight_ceiling", sa.String(), nullable=False),
        sa.Column("hard_guards_fired", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("realistic_timeline_weeks", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_customized", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_user_routines_user_id", "user_routines", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_routines_user_id", table_name="user_routines")
    op.drop_table("user_routines")
