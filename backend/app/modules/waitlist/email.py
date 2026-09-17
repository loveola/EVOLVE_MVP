from typing import Optional
import logging

logger = logging.getLogger("evolve.waitlist.email")

WAITLIST_CONFIRMATION_SUBJECT = "Your EVOLVE Waitlist Confirmation"

WAITLIST_CONFIRMATION_BODY_TEMPLATE = (
    "Hello {recipient_name},\n\n"
    "Thank you for joining the EVOLVE waitlist. Your details have been received and your spot is confirmed.\n\n"
    "While our tailored routine builder is focused on day-to-day haircare, our priority is always your health and progress. "
    "We will notify you as soon as specialized support and new openings become available.\n\n"
    "If you have an exportable consultation summary from your assessment, be sure to keep it handy for your appointments.\n\n"
    "Warm regards,\n"
    "The EVOLVE Team"
)


def send_waitlist_confirmation_email(
    email: str,
    name: Optional[str] = None,
    flag_code: Optional[str] = None
) -> bool:
    recipient_name = name.strip() if name and name.strip() else "there"
    message_body = WAITLIST_CONFIRMATION_BODY_TEMPLATE.format(recipient_name=recipient_name)
    subject = WAITLIST_CONFIRMATION_SUBJECT

    logger.info("Sending waitlist confirmation email to %s (subject: %s, flag: %s)", email, subject, flag_code)
    return True
