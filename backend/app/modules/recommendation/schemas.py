from typing import Literal, Optional
from pydantic import BaseModel, Field

ConcernType = Literal[
    "breakage",
    "dryness",
    "split_ends",
    "length_retention",
    "scalp",
    "tangling",
    "over_conditioning",
]

ProductWeightCeiling = Literal["ultralight", "light", "medium", "rich"]


class RecommendationRequest(BaseModel):
    concern: ConcernType = Field(..., description="User-selected primary concern")
    tier: Optional[str] = Field(default=None, description="Hair ID tier, e.g. GREEN, AMBER, RED")


class PhaseAction(BaseModel):
    id: Optional[str] = None
    type: str
    instruction: Optional[str] = None
    class_: Optional[str] = Field(default=None, alias="class")
    cadence: Optional[str] = None
    evidence: Optional[str] = None
    caution_note: Optional[str] = None

    model_config = {"populate_by_name": True, "extra": "allow"}



class Phase(BaseModel):
    phase: int
    name: str
    days: str
    actions: list[PhaseAction] = Field(default_factory=list)
    checkpoint_day: Optional[int] = None
    checkpoint_metric: Optional[str] = None


class RecommendationResponse(BaseModel):
    user_id: str
    active_problems: list[str]
    cause_explanation_keys: list[str]
    protocols: list[str]
    roadmap: list[Phase]
    product_weight_ceiling: ProductWeightCeiling
    hard_guards_fired: list[str]
    realistic_timeline_weeks: dict
    is_customized: bool = False
    admin_notes: Optional[str] = None


class AdminRoutineUpdate(BaseModel):
    roadmap: Optional[list[Phase]] = None
    admin_notes: Optional[str] = None
    product_weight_ceiling: Optional[ProductWeightCeiling] = None

