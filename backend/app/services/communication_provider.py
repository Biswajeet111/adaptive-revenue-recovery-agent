from dataclasses import dataclass


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
            provider_message_id=(
                f"TEST-EMAIL-{idempotency_key}"
            ),
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
            provider_message_id=(
                f"TEST-SMS-{idempotency_key}"
            ),
        )