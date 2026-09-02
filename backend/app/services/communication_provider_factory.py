from backend.app.config import settings
from backend.app.services.communication_provider import (
    CommunicationProvider,
    SMTPEmailProvider,
)


def build_communication_providers() -> dict[str, CommunicationProvider]:
    """
    Build production communication providers from application settings.

    Email is enabled only when all required SMTP configuration
    values are available.
    """

    providers: dict[str, CommunicationProvider] = {}

    smtp_configured = all(
        [
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.smtp_from_email,
        ]
    )

    if smtp_configured:
        providers["email"] = SMTPEmailProvider(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            from_email=settings.smtp_from_email,
            use_tls=settings.smtp_use_tls,
        )

    return providers