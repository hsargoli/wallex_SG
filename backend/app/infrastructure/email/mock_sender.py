import structlog
from app.domain.ports.email_sender import EmailSenderPort

log = structlog.get_logger("email.mock")

class MockEmailSender(EmailSenderPort):
    async def send(self, to: str, subject: str, body: str) -> None:
        log.info("MOCK_EMAIL_SENT", to=to, subject=subject, body=body)
        print(f"\n{'='*50}\n📧 MOCK EMAIL TO: {to}\nSUBJECT: {subject}\nBODY:\n{body}\n{'='*50}\n")
