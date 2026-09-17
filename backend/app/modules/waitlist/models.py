from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Text, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    flag_code = Column(String, nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=func.now(), nullable=False)
