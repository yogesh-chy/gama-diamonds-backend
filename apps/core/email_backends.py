"""
Custom Django email backend that sends emails via the Resend HTTP API.

Usage:
    1. pip install resend
    2. Set EMAIL_BACKEND = "core.email_backends.ResendEmailBackend"
    3. Set RESEND_API_KEY in your environment variables
    4. Set DEFAULT_FROM_EMAIL = "Gama Diamonds <noreply@yourdomain.com>"
       (must be a verified domain/sender on Resend)
"""
import logging

import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """Sends emails through the Resend HTTP API instead of SMTP."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, "RESEND_API_KEY", "")

    def send_messages(self, email_messages):
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY is not set in Django settings.")
            logger.error("RESEND_API_KEY is not set. Cannot send emails.")
            return 0

        resend.api_key = self.api_key
        sent_count = 0

        for message in email_messages:
            try:
                from_email = message.from_email or settings.DEFAULT_FROM_EMAIL

                params = {
                    "from": from_email,
                    "to": list(message.to),
                    "subject": message.subject,
                    "text": message.body,
                }

                # Include HTML content if available
                if message.alternatives:
                    for content, mimetype in message.alternatives:
                        if mimetype == "text/html":
                            params["html"] = content
                            break
                elif hasattr(message, "html_message") and message.html_message:
                    params["html"] = message.html_message

                resend.Emails.send(params)
                sent_count += 1

            except Exception as e:
                logger.error("Resend email send failed: %s", e)
                if not self.fail_silently:
                    raise

        return sent_count
