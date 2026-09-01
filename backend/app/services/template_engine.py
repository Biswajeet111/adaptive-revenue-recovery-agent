from dataclasses import dataclass
from string import Formatter


@dataclass(frozen=True)
class MessageTemplate:
    name: str
    version: str
    channel: str
    subject: str | None
    body: str


class TemplateEngine:
    """
    Controlled customer communication template engine.

    Templates are deterministic and versioned.
    The engine does not generate arbitrary customer-facing
    content. It only renders explicitly approved variables.
    """

    TEMPLATES: dict[tuple[str, str, str], MessageTemplate] = {
        (
            "payment_recovery",
            "1.0",
            "email",
        ): MessageTemplate(
            name="payment_recovery",
            version="1.0",
            channel="email",
            subject="Complete your payment",
            body=(
                "Hi {customer_name},\n\n"
                "Your payment of {currency} {amount} "
                "could not be completed.\n\n"
                "You can securely complete your payment "
                "using the link below:\n\n"
                "{payment_link}\n\n"
                "This payment link is available until "
                "{expiry}.\n\n"
                "Thank you."
            ),
        ),

        (
            "payment_recovery",
            "1.0",
            "sms",
        ): MessageTemplate(
            name="payment_recovery",
            version="1.0",
            channel="sms",
            subject=None,
            body=(
                "Hi {customer_name}, your payment of "
                "{currency} {amount} could not be completed. "
                "Complete it securely here: {payment_link}. "
                "Available until {expiry}."
            ),
        ),

        (
            "partial_payment_received",
            "1.0",
            "email",
        ): MessageTemplate(
            name="partial_payment_received",
            version="1.0",
            channel="email",
            subject="Partial payment received",
            body=(
                "Hi {customer_name},\n\n"
                "We received {currency} {recovered_amount} "
                "toward your outstanding payment.\n\n"
                "The remaining amount is "
                "{currency} {remaining_amount}.\n\n"
                "You can complete the remaining payment "
                "using the link below:\n\n"
                "{payment_link}\n\n"
                "Thank you."
            ),
        ),

        (
            "payment_recovered",
            "1.0",
            "email",
        ): MessageTemplate(
            name="payment_recovered",
            version="1.0",
            channel="email",
            subject="Payment successfully received",
            body=(
                "Hi {customer_name},\n\n"
                "Your payment of {currency} {amount} "
                "has been successfully received.\n\n"
                "Thank you."
            ),
        ),
    }

    # Explicit allow-list of variables for every template.
    ALLOWED_VARIABLES: dict[
        tuple[str, str, str],
        set[str],
    ] = {
        (
            "payment_recovery",
            "1.0",
            "email",
        ): {
            "customer_name",
            "currency",
            "amount",
            "payment_link",
            "expiry",
        },

        (
            "payment_recovery",
            "1.0",
            "sms",
        ): {
            "customer_name",
            "currency",
            "amount",
            "payment_link",
            "expiry",
        },

        (
            "partial_payment_received",
            "1.0",
            "email",
        ): {
            "customer_name",
            "currency",
            "recovered_amount",
            "remaining_amount",
            "payment_link",
        },

        (
            "payment_recovered",
            "1.0",
            "email",
        ): {
            "customer_name",
            "currency",
            "amount",
        },
    }

    def get_template(
        self,
        name: str,
        version: str,
        channel: str,
    ) -> MessageTemplate:

        key = (
            name,
            version,
            channel,
        )

        template = self.TEMPLATES.get(key)

        if template is None:
            raise ValueError(
                f"Communication template not found: "
                f"{name} v{version} ({channel})"
            )

        return template

    def get_allowed_variables(
        self,
        name: str,
        version: str,
        channel: str,
    ) -> set[str]:

        key = (
            name,
            version,
            channel,
        )

        variables = self.ALLOWED_VARIABLES.get(key)

        if variables is None:
            raise ValueError(
                f"No variable policy found for template: "
                f"{name} v{version} ({channel})"
            )

        return set(variables)

    def _extract_variables(
        self,
        template: str,
    ) -> set[str]:

        variables: set[str] = set()

        formatter = Formatter()

        for _, field_name, _, _ in formatter.parse(
            template
        ):

            if field_name is None:
                continue

            if (
                not field_name.isidentifier()
            ):
                raise ValueError(
                    "Invalid template variable: "
                    f"{field_name}"
                )

            variables.add(
                field_name
            )

        return variables

    def render(
        self,
        *,
        name: str,
        version: str,
        channel: str,
        variables: dict[str, object],
    ) -> MessageTemplate:

        template = self.get_template(
            name=name,
            version=version,
            channel=channel,
        )

        allowed_variables = (
            self.get_allowed_variables(
                name=name,
                version=version,
                channel=channel,
            )
        )

        template_variables = (
            self._extract_variables(
                template.body
            )
        )

        undeclared_variables = (
            template_variables
            - allowed_variables
        )

        if undeclared_variables:
            raise ValueError(
                "Template contains variables that "
                "are not approved by the communication "
                "variable policy: "
                f"{sorted(undeclared_variables)}"
            )

        supplied_variables = set(
            variables.keys()
        )

        unknown_variables = (
            supplied_variables
            - allowed_variables
        )

        if unknown_variables:
            raise ValueError(
                "Unknown communication variables: "
                f"{sorted(unknown_variables)}"
            )

        missing_variables = (
            template_variables
            - supplied_variables
        )

        if missing_variables:
            raise ValueError(
                "Missing communication variables: "
                f"{sorted(missing_variables)}"
            )

        rendered_body = template.body.format(
            **variables
        )

        rendered_subject = None

        if template.subject is not None:

            rendered_subject = (
                template.subject.format(
                    **variables
                )
            )

        return MessageTemplate(
            name=template.name,
            version=template.version,
            channel=template.channel,
            subject=rendered_subject,
            body=rendered_body,
        )