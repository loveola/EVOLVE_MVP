from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class WarningFlag(BaseModel):
    affects: str
    message: str

class HairTraits(BaseModel):
    scalp_type: str
    porosity: str
    elasticity: str
    thickness: str
    density: str

class AssessmentResult(BaseModel):
    traits: HairTraits
    flags: List[WarningFlag] = Field(default_factory=list)

class AssessmentDraftRequest(BaseModel):
    current_step: str = Field(default="A", description="Current assessment step: A, B, C, D, E, F")
    answers: Dict[str, Any] = Field(default_factory=dict)

class AssessmentSubmitRequest(BaseModel):
    answers: Dict[str, Any] = Field(..., description="Finalized answers dictionary")

class AssessmentResponse(BaseModel):
    user_id: str
    status: str
    current_step: str
    answers: Dict[str, Any] = Field(default_factory=dict)
    results: Optional[AssessmentResult] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
