from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

ConcernType = Literal[
    "breakage",
    "dryness",
    "split_ends",
    "length_retention",
    "stunted_growth",
    "scalp",
    "tangling",
    "over_conditioning",
    "hygral_fatigue",
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
    current_phase: int = 1
    current_day: int = 1
    started_at: Optional[datetime] = None
    completed_actions: list[str] = Field(default_factory=list)
    progress_percentage: int = 0


class RoutineProgressUpdate(BaseModel):
    current_phase: Optional[int] = Field(None, ge=1, le=10)
    current_day: Optional[int] = Field(None, ge=1, le=365)
    completed_actions: Optional[list[str]] = Field(None, max_length=100)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    started_at: Optional[datetime] = None


class AdminRoutineUpdate(BaseModel):
    roadmap: Optional[list[Phase]] = None
    admin_notes: Optional[str] = None
    product_weight_ceiling: Optional[ProductWeightCeiling] = None


class AdminRuleResponse(BaseModel):
    problem_id: str
    display_name: str
    priority: int
    is_active: bool
    protocol_id: str
    classifier: dict
    score_boosters: list
    hard_guards: list
    realistic_timeline_weeks: dict
    root_cause_explanation_key: str
    always_runs_as_module: bool


class AdminRuleUpdate(BaseModel):
    display_name: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    classifier: Optional[dict] = None
    score_boosters: Optional[list] = None
    hard_guards: Optional[list] = None
    realistic_timeline_weeks: Optional[dict] = None
    protocol_id: Optional[str] = None


class AdminProtocolResponse(BaseModel):
    id: str
    name: str
    problem_id: Optional[str] = None
    phases: list[dict]
    is_active: bool


class AdminProtocolUpdate(BaseModel):
    name: Optional[str] = None
    problem_id: Optional[str] = None
    phases: Optional[list[dict]] = None
    is_active: Optional[bool] = None


