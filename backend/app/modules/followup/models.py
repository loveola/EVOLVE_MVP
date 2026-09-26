import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class Followup(Base):
    __tablename__ = "followups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    routine_id = Column(UUID(as_uuid=True), ForeignKey("user_routines.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_week = Column(Integer, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(30), nullable=False, server_default="scheduled", default="scheduled", index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    response_rating = Column(String(30), nullable=True)
    response_notes = Column(Text, nullable=True)
    response_symptoms = Column(JSONB().with_variant(JSON(), "sqlite"), nullable=False, server_default="[]", default=list)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    action_taken = Column(String(30), nullable=True)
    user_email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4())
        kwargs.setdefault("status", "scheduled")
        kwargs.setdefault("response_symptoms", [])
        kwargs.setdefault("sent_at", None)
        kwargs.setdefault("response_rating", None)
        kwargs.setdefault("response_notes", None)
        kwargs.setdefault("completed_at", None)
        kwargs.setdefault("action_taken", None)
        kwargs.setdefault("user_email", None)
        super().__init__(**kwargs)
