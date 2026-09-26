from typing import Optional
import logging
import uuid
import httpx
from app.core.config import settings

logger = logging.getLogger("evolve.followup.email")


def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    masked_local = (local[0] + "***") if len(local) > 0 else "***"
    return f"{masked_local}@{domain}"


def send_followup_notification_email(
    email: str,
    name: Optional[str],
    scheduled_week: int,
    followup_id: uuid.UUID
) -> bool:
    if not settings.RESEND_API_KEY:
        logger.info("Resend API key not configured; skipping followup dispatch")
        return False

    recipient_name = name.strip() if name and name.strip() else "there"
    subject = f"EVOLVE: Week {scheduled_week} Hair Routine Check-In"

    html_content = (
        f"<p>Hello {recipient_name},</p>"
        f"<p>It is time for your Week {scheduled_week} hair routine check-in.</p>"
        f"<p>Please let us know how your hair is responding to your personalized protocol.</p>"
        f"<p><a href=\"https://evolve.app/followup/{followup_id}\">Complete Your Check-In</a></p>"
        f"<p>Best regards,<br>The EVOLVE Team</p>"
    )

    text_content = (
        f"Hello {recipient_name},\n\n"
        f"It is time for your Week {scheduled_week} hair routine check-in.\n"
        f"Please let us know how your hair is responding to your personalized protocol.\n\n"
        f"Complete your check-in: https://evolve.app/followup/{followup_id}\n\n"
        f"Best regards,\n"
        f"The EVOLVE Team"
    )

    masked = mask_email(email)
    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [email],
        "subject": subject,
        "html": html_content,
        "text": text_content,
    }

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        if response.status_code in [200, 201]:
            logger.info("Followup email sent via Resend to %s", masked)
            return True
        logger.error("Resend API returned error status %d for recipient %s", response.status_code, masked)
        return False
    except Exception as exc:
        logger.error("Failed to dispatch email via Resend to %s: %s", masked, type(exc).__name__)
        return False
