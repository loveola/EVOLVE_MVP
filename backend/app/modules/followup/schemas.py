import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CheckInSubmission(BaseModel):
    response_rating: str
    response_notes: Optional[str] = Field(None, max_length=2000)
    response_symptoms: Optional[list[str]] = Field(default_factory=list, max_length=50)

    @field_validator("response_rating")
    @classmethod
    def validate_response_rating(cls, v: str) -> str:
        allowed = {"improving", "no_change", "worse", "severe_reaction"}
        if v not in allowed:
            raise ValueError(f"Invalid rating: {v}. Must be one of {sorted(allowed)}")
        return v

    @field_validator("response_symptoms", mode="before")
    @classmethod
    def default_symptoms_list(cls, v):
        if v is None:
            return []
        return v


class FollowupResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    routine_id: uuid.UUID
    scheduled_week: int
    due_date: datetime
    status: str
    sent_at: Optional[datetime] = None
    response_rating: Optional[str] = None
    response_notes: Optional[str] = None
    response_symptoms: list[str] = Field(default_factory=list)
    completed_at: Optional[datetime] = None
    action_taken: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CheckInResultResponse(BaseModel):
    followup: FollowupResponse
    action_taken: str
    message: str
    escalated: bool = False
    escalation_advisory: Optional[str] = None
    current_phase: Optional[int] = None

    model_config = {"from_attributes": True}
