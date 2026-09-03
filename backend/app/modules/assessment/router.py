from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.core.database import get_db
from app.modules.assessment.models import HairAssessment
from app.modules.assessment.schemas import (
    AssessmentDraftRequest,
    AssessmentSubmitRequest,
    AssessmentResponse,
    AssessmentResult
)
from app.modules.assessment.engine import evaluate_assessment
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/assessment", tags=["Hair ID Assessment"])

@router.get("/me", response_model=AssessmentResponse)
def get_my_assessment(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if db is not None:
        user_uuid = uuid.UUID(current_user.uid)
        record = db.query(HairAssessment).filter(HairAssessment.user_id == user_uuid).first()
        if record:
            results_data = AssessmentResult(**record.results) if record.results else None
            return AssessmentResponse(
                user_id=str(record.user_id),
                status=record.status,
                current_step=record.current_step,
                answers=record.answers or {},
                results=results_data,
                updated_at=record.updated_at
            )

    return AssessmentResponse(
        user_id=current_user.uid,
        status="not_started",
        current_step="A",
        answers={},
        results=None,
        updated_at=datetime.now(timezone.utc)
    )

@router.put("/me", response_model=AssessmentResponse)
def save_assessment_progress(
    payload: AssessmentDraftRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    user_uuid = uuid.UUID(current_user.uid)

    if db is not None:
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

    return AssessmentResponse(
        user_id=current_user.uid,
        status="in_progress",
        current_step=payload.current_step,
        answers=payload.answers,
        results=None,
        updated_at=now
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

    if db is not None:
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

    return AssessmentResponse(
        user_id=current_user.uid,
        status="completed",
        current_step="completed",
        answers=payload.answers,
        results=AssessmentResult(**evaluation),
        updated_at=now
    )
