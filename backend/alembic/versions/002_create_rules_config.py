"""create rules_config and derived_variable_config tables

Revision ID: 002_create_rules_config
Revises: 001_create_hair_assessments
Create Date: 2026-09-09 17:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "002_create_rules_config"
down_revision: Union[str, None] = "001_create_hair_assessments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    op.create_table(
        "rules_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("problem_id", sa.String(), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("replaces", sa.String(), nullable=True),
        sa.Column("classifier", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("score_boosters", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("hard_guards", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("protocol_id", sa.String(), nullable=False),
        sa.Column("primary_metric", sa.String(), nullable=True),
        sa.Column("root_cause_explanation_key", sa.String(), nullable=False),
        sa.Column("realistic_timeline_weeks", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("always_runs_as_module", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "derived_variable_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("var_type", sa.String(), nullable=False),
        sa.Column("rule_text", sa.Text(), nullable=False),
        sa.Column("consumes", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("effect_text", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("derived_variable_config")
    op.drop_table("rules_config")
