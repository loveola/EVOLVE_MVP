from datetime import datetime, timezone, timedelta
from typing import Optional, Callable
from sqlalchemy.orm import Session

from app.modules.recommendation.models import UserRoutine
from app.modules.followup.models import Followup
from app.modules.assessment.models import EscalationEvent
from app.modules.followup.schemas import CheckInSubmission, CheckInResultResponse, FollowupResponse


def schedule_routine_followups(routine: UserRoutine, db: Session) -> list[Followup]:
    base_date = getattr(routine, "started_at", None) or getattr(routine, "created_at", None) or datetime.now(timezone.utc)
    if base_date.tzinfo is None:
        base_date = base_date.replace(tzinfo=timezone.utc)

    existing = db.query(Followup).filter(Followup.routine_id == routine.id).all()
    existing_weeks = set()
    for item in existing:
        week = getattr(item, "scheduled_week", None)
        if isinstance(week, int):
            existing_weeks.add(week)

    created = []
    for week in [2, 4, 8]:
        if week in existing_weeks:
            continue
        due_date = base_date + timedelta(weeks=week)
        followup = Followup(
            user_id=routine.user_id,
            routine_id=routine.id,
            scheduled_week=week,
            due_date=due_date,
            status="scheduled",
        )
        db.add(followup)
        created.append(followup)

    db.flush()
    return created


def dispatch_due_followups(db: Session, email_sender: Optional[Callable[[Followup], bool]] = None) -> int:
    now = datetime.now(timezone.utc)
    due_followups = db.query(Followup).filter(
        Followup.status.in_(["scheduled", "due"]),
        Followup.due_date <= now,
    ).all()

    count = 0
    for followup in due_followups:
        if email_sender is not None:
            success = email_sender(followup)
            if success is False:
                continue
        followup.status = "sent"
        followup.sent_at = now
        count += 1

    db.commit()
    return count


def _is_severe_symptom(symptoms: Optional[list[str]]) -> bool:
    if not symptoms:
        return False
    indicators = {
        "severe_reaction",
        "severe_burning",
        "severe_itching",
        "blistering",
        "burning",
        "swelling",
        "hives",
        "infection",
        "bleeding",
        "hair_loss",
    }
    for symptom in symptoms:
        s_lower = str(symptom).lower()
        if s_lower in indicators or "severe" in s_lower or "burn" in s_lower or "blister" in s_lower:
            return True
    return False


def process_check_in(followup: Followup, submission: CheckInSubmission, db: Session) -> CheckInResultResponse:
    now = datetime.now(timezone.utc)
    followup.completed_at = now
    followup.status = "completed"
    followup.response_rating = submission.response_rating
    followup.response_notes = submission.response_notes
    followup.response_symptoms = submission.response_symptoms or []

    routine = db.query(UserRoutine).filter(UserRoutine.id == followup.routine_id).first()
    if not routine and followup.user_id:
        routine = db.query(UserRoutine).filter(UserRoutine.user_id == followup.user_id).first()

    if submission.response_rating in ("worse", "severe_reaction") or _is_severe_symptom(submission.response_symptoms):
        # // check escalation engine
        flag_code = "CHECKIN_ESCALATION" if submission.response_rating != "severe_reaction" else "SEVERE_REACTION"
        symptoms_suffix = f" with symptoms: {', '.join(submission.response_symptoms)}" if submission.response_symptoms else ""
        trigger_reason = f"Check-in Week {followup.scheduled_week} reported {submission.response_rating}{symptoms_suffix}"
        event = EscalationEvent(
            user_id=followup.user_id,
            flag_code=flag_code,
            trigger_reason=trigger_reason,
            assessment_id=getattr(routine, "assessment_id", None),
        )
        db.add(event)
        followup.action_taken = "escalated"
        db.commit()
        db.refresh(followup)
        return CheckInResultResponse(
            followup=FollowupResponse.model_validate(followup),
            action_taken="escalated",
            message="Your check-in has been escalated for review by our hair care specialists.",
            escalated=True,
            escalation_advisory="We recommend pausing active treatments and reviewing your current routine.",
            current_phase=getattr(routine, "current_phase", None),
        )
    elif submission.response_rating in ("improving", "no_change"):
        total_phases = 4
        if routine and isinstance(getattr(routine, "roadmap", None), list) and len(routine.roadmap) > 0:
            total_phases = len(routine.roadmap)
        if routine and routine.current_phase < total_phases:
            routine.current_phase += 1
            followup.action_taken = "advanced_phase"
            message = "Great progress! Your routine has been advanced to the next phase."
        elif routine and routine.current_phase >= total_phases:
            followup.action_taken = "maintained"
            message = "Routine maintained at maximum phase."
        else:
            followup.action_taken = "advanced_phase"
            message = "Great progress! Your routine has been advanced to the next phase."
        db.commit()
        db.refresh(followup)
        return CheckInResultResponse(
            followup=FollowupResponse.model_validate(followup),
            action_taken=followup.action_taken,
            message=message,
            escalated=False,
            escalation_advisory=None,
            current_phase=getattr(routine, "current_phase", None),
        )

    db.commit()
    db.refresh(followup)
    return CheckInResultResponse(
        followup=FollowupResponse.model_validate(followup),
        action_taken=followup.action_taken or "completed",
        message="Your check-in has been completed.",
        escalated=False,
        escalation_advisory=None,
        current_phase=getattr(routine, "current_phase", None),
    )
