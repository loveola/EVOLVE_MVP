from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.modules.assessment.models import Base
import uuid


class RulesConfig(Base):
    __tablename__ = "rules_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    problem_id = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    replaces = Column(String, nullable=True)
    classifier = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    score_boosters = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    hard_guards = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    protocol_id = Column(String, nullable=False)
    primary_metric = Column(String, nullable=True)
    root_cause_explanation_key = Column(String, nullable=False)
    realistic_timeline_weeks = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    always_runs_as_module = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    priority = Column(Integer, nullable=False, default=50, server_default=text("50"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DerivedVariableConfig(Base):
    __tablename__ = "derived_variable_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    name = Column(String, nullable=False, unique=True)
    var_type = Column(String, nullable=False)
    rule_text = Column(Text, nullable=False)
    consumes = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    effect_text = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
