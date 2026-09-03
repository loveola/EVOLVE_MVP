from fastapi import APIRouter, Depends, status
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.assessment.schemas import (
    AssessmentDraftRequest,
    AssessmentSubmitRequest,
    AssessmentResponse,
    AssessmentResult
)
from app.modules.assessment.engine import evaluate_assessment
from datetime import datetime, timezone

router = APIRouter(prefix="/assessment", tags=["Hair ID Assessment"])

# State store for active assessment sessions
_assessments_store = {}

@router.get("/me", response_model=AssessmentResponse)
async def get_my_assessment(current_user: UserResponse = Depends(get_current_user)):
    data = _assessments_store.get(current_user.uid)
    if not data:
        return AssessmentResponse(
            user_id=current_user.uid,
            status="not_started",
            current_step="A",
            answers={},
            results=None
        )
    return data

@router.put("/me", response_model=AssessmentResponse)
async def save_assessment_progress(
    payload: AssessmentDraftRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    record = AssessmentResponse(
        user_id=current_user.uid,
        status="in_progress",
        current_step=payload.current_step,
        answers=payload.answers,
        results=None,
        updated_at=datetime.now(timezone.utc)
    )
    _assessments_store[current_user.uid] = record
    return record

@router.post("/submit", response_model=AssessmentResponse)
async def submit_assessment(
    payload: AssessmentSubmitRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    evaluation = evaluate_assessment(payload.answers)
    record = AssessmentResponse(
        user_id=current_user.uid,
        status="completed",
        current_step="completed",
        answers=payload.answers,
        results=AssessmentResult(**evaluation),
        updated_at=datetime.now(timezone.utc)
    )
    _assessments_store[current_user.uid] = record
    return record
