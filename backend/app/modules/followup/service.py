from datetime import datetime, timezone, timedelta
from typing import Optional, Callable
from sqlalchemy.orm import Session

from app.modules.recommendation.models import UserRoutine
from app.modules.followup.models import Followup


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


def dispatch_due_followups(db: Session, email_sender: Optional[Callable] = None) -> int:
    now = datetime.now(timezone.utc)
    due_followups = db.query(Followup).filter(
        Followup.status.in_(["scheduled", "due"]),
        Followup.due_date <= now,
    ).all()

    count = 0
    for followup in due_followups:
        followup.status = "sent"
        followup.sent_at = now
        if email_sender is not None:
            try:
                email_sender(followup)
            except TypeError:
                try:
                    email_sender(str(followup.user_id), None, followup.scheduled_week, followup.id)
                except TypeError:
                    try:
                        email_sender()
                    except TypeError:
                        pass
        count += 1

    db.commit()
    return count
