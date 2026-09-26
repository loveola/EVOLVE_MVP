import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.modules.waitlist.models import WaitlistEntry
from app.modules.waitlist.schemas import WaitlistRequest, WaitlistResponse
from app.modules.waitlist import email as waitlist_email

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("", response_model=WaitlistResponse, status_code=status.HTTP_201_CREATED)
def submit_waitlist(
    payload: WaitlistRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    entry_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    normalized_email = payload.email.lower().strip()
    clean_name = payload.name.strip() if payload.name and payload.name.strip() else None

    entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == normalized_email).first()
    is_new = False
    if not entry:
        is_new = True
        entry = WaitlistEntry(
            id=entry_id,
            email=normalized_email,
            name=clean_name,
            flag_code=payload.flag_code,
            notes=payload.notes,
            created_at=now,
            updated_at=now
        )
        db.add(entry)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == normalized_email).first()
            is_new = False
            if entry:
                if clean_name:
                    entry.name = clean_name
                if payload.flag_code:
                    entry.flag_code = payload.flag_code
                if payload.notes:
                    entry.notes = payload.notes
                entry.updated_at = now
                db.commit()
    else:
        if clean_name:
            entry.name = clean_name
        if payload.flag_code:
            entry.flag_code = payload.flag_code
        if payload.notes:
            entry.notes = payload.notes
        entry.updated_at = now
        db.commit()

    db.refresh(entry)

    if is_new:
        background_tasks.add_task(
            waitlist_email.send_waitlist_confirmation_email,
            email=normalized_email,
            name=clean_name,
            flag_code=payload.flag_code
        )

    return WaitlistResponse(
        id=str(entry.id),
        email=entry.email,
        name=entry.name,
        flag_code=payload.flag_code if not is_new else entry.flag_code,
        notes=payload.notes if not is_new else entry.notes,
        created_at=entry.created_at,
        message="Waitlist signup confirmed. A confirmation email has been sent." if is_new else "Waitlist entry updated."
    )
