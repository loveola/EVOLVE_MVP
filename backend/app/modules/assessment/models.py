from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid


class HairAssessment(Base):
    __tablename__ = "hair_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    answers = Column(JSONB, nullable=False, default=dict)
    results = Column(JSONB, nullable=True)
    status = Column(String, nullable=False, default="in_progress")
    current_step = Column(String, nullable=False, default="A")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=func.now(), nullable=False)


class EscalationEvent(Base):
    __tablename__ = "escalation_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("hair_assessments.id", ondelete="SET NULL"), nullable=True, index=True)
    flag_code = Column(String, nullable=False, index=True)
    trigger_reason = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
