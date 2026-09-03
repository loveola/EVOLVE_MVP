from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class HairAssessment(Base):
    __tablename__ = "hair_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    answers = Column(JSONB, nullable=False, default=dict)
    results = Column(JSONB, nullable=True)
    status = Column(String, nullable=False, default="in_progress")
    current_step = Column(String, nullable=False, default="A")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
