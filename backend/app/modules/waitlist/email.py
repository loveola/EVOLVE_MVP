from typing import Optional
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger("evolve.waitlist.email")

WAITLIST_CONFIRMATION_SUBJECT = "You're on the EVOLVE Waitlist"

WAITLIST_CONFIRMATION_BODY_TEMPLATE = (
    "Hello {recipient_name},\n\n"
    "Thank you for joining the EVOLVE waitlist. We have received your details and your spot is confirmed.\n\n"
    "We will reach out as soon as new openings become available.\n\n"
    "Warm regards,\n"
    "The EVOLVE Team"
)


def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    masked_local = (local[0] + "***") if len(local) > 0 else "***"
    return f"{masked_local}@{domain}"


def send_waitlist_confirmation_email(
    email: str,
    name: Optional[str] = None,
    flag_code: Optional[str] = None,
    custom_subject: Optional[str] = None,
    custom_body: Optional[str] = None
) -> bool:
    recipient_name = name.strip() if name and name.strip() else "there"
    message_body = custom_body if custom_body else WAITLIST_CONFIRMATION_BODY_TEMPLATE.format(recipient_name=recipient_name)
    subject = custom_subject if custom_subject else WAITLIST_CONFIRMATION_SUBJECT

    masked = mask_email(email)

    if not settings.RESEND_API_KEY:
        logger.info("Resend API key not configured; skipping dispatch to %s (subject: %s)", masked, subject)
        return True

    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [email],
        "subject": subject,
        "text": message_body
    }

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10.0
        )
        if response.status_code in [200, 201]:
            logger.info("Waitlist confirmation email sent via Resend to %s", masked)
            return True
        else:
            logger.error("Resend API returned error status %d for recipient %s", response.status_code, masked)
            return False
    except Exception as exc:
        logger.error("Failed to dispatch email via Resend to %s: %s", masked, type(exc).__name__)
        return False
