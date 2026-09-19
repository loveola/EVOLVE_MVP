import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.assessment.models import HairAssessment, EscalationEvent
from app.modules.assessment.schemas import (
    AssessmentDraftRequest,
    AssessmentSubmitRequest,
    AssessmentResponse,
    AssessmentResult
)
from app.modules.assessment.engine import evaluate_assessment
from app.modules.recommendation.escalation import evaluate_escalation

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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        record = db.query(HairAssessment).filter(HairAssessment.user_id == user_uuid).first()
        if record:
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
    # // check escalation engine
    escalation_res = evaluate_escalation(payload.answers, db=db)
    evaluation = evaluate_assessment(payload.answers)
    evaluation["tier"] = escalation_res.tier
    evaluation["flag_code"] = escalation_res.flag_code
    evaluation["trigger_reason"] = escalation_res.trigger_reason
    evaluation["escalation_flags"] = [f.get("flag_code") or f.get("id") for f in escalation_res.fired_flags]
    if escalation_res.requires_escalation:
        evaluation["referral_summary"] = escalation_res.referral_summary
        status_val = "escalated"
    else:
        status_val = "completed"

    now = datetime.now(timezone.utc)
    user_uuid = uuid.UUID(current_user.uid)

    record = db.query(HairAssessment).filter(HairAssessment.user_id == user_uuid).first()
    if not record:
        assessment_id = uuid.uuid4()
        record = HairAssessment(
            id=assessment_id,
            user_id=user_uuid,
            answers=payload.answers,
            results=evaluation,
            status=status_val,
            current_step="completed",
            updated_at=now
        )
        db.add(record)
    else:
        assessment_id = record.id
        record.answers = payload.answers
        record.results = evaluation
        record.status = status_val
        record.current_step = "completed"
        record.updated_at = now

    if escalation_res.requires_escalation:
        event = EscalationEvent(
            user_id=user_uuid,
            assessment_id=assessment_id,
            flag_code=escalation_res.flag_code,
            trigger_reason=escalation_res.trigger_reason,
            timestamp=now,
            created_at=now
        )
        db.add(event)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        record = db.query(HairAssessment).filter(HairAssessment.user_id == user_uuid).first()
        if record:
            assessment_id = record.id
            record.answers = payload.answers
            record.results = evaluation
            record.status = status_val
            record.current_step = "completed"
            record.updated_at = now
            if escalation_res.requires_escalation:
                event = EscalationEvent(
                    user_id=user_uuid,
                    assessment_id=assessment_id,
                    flag_code=escalation_res.flag_code,
                    trigger_reason=escalation_res.trigger_reason,
                    timestamp=now,
                    created_at=now
                )
                db.add(event)
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
