import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.followup.models import Followup
from app.modules.followup.schemas import (
    CheckInSubmission,
    CheckInResultResponse,
    FollowupResponse,
)
from app.modules.followup.service import process_check_in

router = APIRouter(prefix="/followups", tags=["Followups"])


def _extract_user_uuid(user: UserResponse) -> uuid.UUID:
    raw = getattr(user, "uid", None) or getattr(user, "id", None)
    if isinstance(raw, uuid.UUID):
        return raw
    return uuid.UUID(str(raw))


@router.get("/me", response_model=list[FollowupResponse])
def get_my_followups(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_uuid = _extract_user_uuid(current_user)
    followups = (
        db.query(Followup)
        .filter(Followup.user_id == user_uuid)
        .order_by(Followup.due_date.asc())
        .all()
    )
    return followups


@router.get("/me/next", response_model=FollowupResponse)
def get_my_next_followup(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_uuid = _extract_user_uuid(current_user)
    followup = (
        db.query(Followup)
        .filter(
            Followup.user_id == user_uuid,
            Followup.status != "completed",
        )
        .order_by(Followup.due_date.asc())
        .first()
    )
    if not followup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No upcoming follow-up scheduled",
        )
    return followup


@router.post("/{followup_id}/check-in", response_model=CheckInResultResponse)
def submit_check_in(
    followup_id: uuid.UUID,
    payload: CheckInSubmission,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_uuid = _extract_user_uuid(current_user)
    followup = db.query(Followup).filter(Followup.id == followup_id).with_for_update().first()

    if not followup or str(followup.user_id) != str(user_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up not found",
        )

    if followup.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Follow-up check-in has already been completed",
        )

    return process_check_in(followup, payload, db)
