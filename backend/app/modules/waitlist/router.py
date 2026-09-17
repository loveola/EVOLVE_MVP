import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session

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

    entry = WaitlistEntry(
        id=entry_id,
        email=payload.email,
        name=payload.name,
        flag_code=payload.flag_code,
        notes=payload.notes,
        created_at=now,
        updated_at=now
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    background_tasks.add_task(
        waitlist_email.send_waitlist_confirmation_email,
        email=payload.email,
        name=payload.name,
        flag_code=payload.flag_code
    )

    return WaitlistResponse(
        id=str(entry.id),
        email=entry.email,
        name=entry.name,
        flag_code=entry.flag_code,
        notes=entry.notes,
        created_at=entry.created_at,
        message="Waitlist signup confirmed. A confirmation email has been sent."
    )
