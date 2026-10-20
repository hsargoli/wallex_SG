from app.core.config import get_settings
from app.domain.ports.email_sender import EmailSenderPort
from app.infrastructure.email.mock_sender import MockEmailSender


def get_email_sender() -> EmailSenderPort:
    """Factory: Resend in production (if key exists), Mock otherwise."""
    settings = get_settings()
    if settings.RESEND_API_KEY:
        from app.infrastructure.email.resend_sender import ResendEmailSender
        return ResendEmailSender()
    return MockEmailSender()
