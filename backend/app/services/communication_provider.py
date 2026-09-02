from dataclasses import dataclass
import smtplib
from email.message import EmailMessage


@dataclass(frozen=True)
class ProviderResult:
    success: bool
    provider: str
    provider_message_id: str | None = None
    failure_reason: str | None = None


class CommunicationProvider:
    """
    Base abstraction for customer communication providers.
    """

    channel: str = "unknown"
    provider_name: str = "unknown"

    def send(
        self,
        *,
        recipient: str,
        subject: str | None,
        message: str,
        idempotency_key: str,
    ) -> ProviderResult:
        raise NotImplementedError


class TestEmailProvider(CommunicationProvider):
    channel = "email"
    provider_name = "test_email"

    def send(
        self,
        *,
        recipient: str,
        subject: str | None,
        message: str,
        idempotency_key: str,
    ) -> ProviderResult:
        return ProviderResult(
            success=True,
            provider=self.provider_name,
            provider_message_id=f"TEST-EMAIL-{idempotency_key}",
        )


class SMTPEmailProvider(CommunicationProvider):
    """
    Production email provider using SMTP.

    SMTP credentials are supplied by the application settings.
    """

    channel = "email"
    provider_name = "smtp"

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    def send(
        self,
        *,
        recipient: str,
        subject: str | None,
        message: str,
        idempotency_key: str,
    ) -> ProviderResult:

        email = EmailMessage()
        email["From"] = self.from_email
        email["To"] = recipient
        email["Subject"] = subject or "Payment Recovery Notification"
        email["X-Recovery-Idempotency-Key"] = idempotency_key
        email.set_content(message)

        try:
            with smtplib.SMTP(
                self.host,
                self.port,
                timeout=30,
            ) as smtp:

                if self.use_tls:
                    smtp.starttls()

                smtp.login(
                    self.username,
                    self.password,
                )

                smtp.send_message(email)

            return ProviderResult(
                success=True,
                provider=self.provider_name,
                provider_message_id=idempotency_key,
            )

        except Exception as exc:
            return ProviderResult(
                success=False,
                provider=self.provider_name,
                failure_reason=str(exc),
            )


class TestSMSProvider(CommunicationProvider):
    channel = "sms"
    provider_name = "test_sms"

    def send(
        self,
        *,
        recipient: str,
        subject: str | None,
        message: str,
        idempotency_key: str,
    ) -> ProviderResult:
        return ProviderResult(
            success=True,
            provider=self.provider_name,
            provider_message_id=f"TEST-SMS-{idempotency_key}",
        )