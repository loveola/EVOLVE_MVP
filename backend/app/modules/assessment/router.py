import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.assessment.models import HairAssessment
from app.modules.assessment.schemas import (
    AssessmentDraftRequest,
    AssessmentSubmitRequest,
    AssessmentResponse,
    AssessmentResult
)
from app.modules.assessment.engine import evaluate_assessment

router = APIRouter(prefix="/assessment", tags=["Assessment"])

@router.get("/me", response_model=AssessmentResponse)
def get_user_assessment(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_uuid = uuid.UUID(current_user.uid)
    record = db.query(HairAssessment).filter(HairAssessment.user_id == user_uuid).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    results_obj = None
    if record.results:
        results_obj = AssessmentResult(**record.results)

    return AssessmentResponse(
        user_id=str(record.user_id),
        status=record.status,
        current_step=record.current_step,
        answers=record.answers or {},
        results=results_obj,
        updated_at=record.updated_at
    )

@router.put("/me", response_model=AssessmentResponse)
def save_assessment_draft(
    payload: AssessmentDraftRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    user_uuid = uuid.UUID(current_user.uid)

    record = db.query(HairAssessment).filter(HairAssessment.user_id == user_uuid).first()
    if not record:
        record = HairAssessment(
            user_id=user_uuid,
            answers=payload.answers,
            status="in_progress",
            current_step=payload.current_step,
            updated_at=now
        )
        db.add(record)
    else:
        record.answers = payload.answers
        record.current_step = payload.current_step
        record.status = "in_progress"
        record.results = None
        record.updated_at = now
    db.commit()
    db.refresh(record)

    return AssessmentResponse(
        user_id=str(record.user_id),
        status=record.status,
        current_step=record.current_step,
        answers=record.answers or {},
        results=None,
        updated_at=record.updated_at
    )

@router.post("/submit", response_model=AssessmentResponse)
def submit_assessment(
    payload: AssessmentSubmitRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evaluation = evaluate_assessment(payload.answers)
    now = datetime.now(timezone.utc)
    user_uuid = uuid.UUID(current_user.uid)

    record = db.query(HairAssessment).filter(HairAssessment.user_id == user_uuid).first()
    if not record:
        record = HairAssessment(
            user_id=user_uuid,
            answers=payload.answers,
            results=evaluation,
            status="completed",
            current_step="completed",
            updated_at=now
        )
        db.add(record)
    else:
        record.answers = payload.answers
        record.results = evaluation
        record.status = "completed"
        record.current_step = "completed"
        record.updated_at = now
    db.commit()
    db.refresh(record)

    return AssessmentResponse(
        user_id=str(record.user_id),
        status=record.status,
        current_step=record.current_step,
        answers=record.answers or {},
        results=AssessmentResult(**evaluation),
        updated_at=record.updated_at
    )
