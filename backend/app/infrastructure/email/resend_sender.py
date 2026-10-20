import asyncio
import structlog
import resend

from app.domain.ports.email_sender import EmailSenderPort
from app.core.config import get_settings

log = structlog.get_logger("email.resend")


class ResendEmailSender(EmailSenderPort):
    """پیاده‌سازی واقعی ارسال ایمیل با سرویس Resend."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY is missing")
        resend.api_key = settings.RESEND_API_KEY
        self.from_email = settings.EMAIL_FROM

    async def send(self, to: str, subject: str, body: str) -> None:
        # resend SDK sync است، برای اینکه event loop بلاک نشه از to_thread استفاده می‌کنیم
        try:
            await asyncio.to_thread(
                resend.Emails.send,
                {
                    "from": self.from_email,
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
            )
            log.info("RESEND_EMAIL_SENT", to=to, subject=subject)
        except Exception as e:
            log.error("RESEND_EMAIL_FAILED", to=to, error=str(e))
            raise
