from dataclasses import dataclass
from typing import Literal


CommunicationChannel = Literal[
    "email",
    "sms",
]


CommunicationDecision = Literal[
    "allowed",
    "blocked",
    "escalated",
]


@dataclass(frozen=True)
class CommunicationPolicyDecision:
    decision: CommunicationDecision
    channel: CommunicationChannel | None
    template_name: str | None
    template_version: str | None
    reason: str
    allowed_variables: frozenset[str]


class CommunicationPolicyService:
    """
    Deterministic enforcement of Communication Policy v1.0.

    The AI may recommend a recovery action, but it does not
    authorize customer communication. This service enforces
    the communication policy before a message can be created.
    """

    POLICY_NAME = "Communication Policy"
    POLICY_VERSION = "1.0"

    INTERNAL_FIELDS = frozenset(
        {
            "failure_code",
            "failure_reason",
            "risk_score",
            "classification",
            "recoverability",
        }
    )

    PAYMENT_RECOVERY_VARIABLES = frozenset(
        {
            "customer_name",
            "currency",
            "amount",
            "payment_link",
            "expiry",
        }
    )

    PARTIAL_RECOVERY_VARIABLES = frozenset(
        {
            "customer_name",
            "currency",
            "recovered_amount",
            "remaining_amount",
            "payment_link",
        }
    )

    SUCCESS_VARIABLES = frozenset(
        {
            "customer_name",
            "currency",
            "amount",
        }
    )

    def evaluate(
        self,
        *,
        action_type: str,
        recovery_case_status: str,
        recovery_action_status: str,
        payment_link_created: bool = False,
        recovery_confirmed: bool = False,
        channel: CommunicationChannel = "email",
    ) -> CommunicationPolicyDecision:

        # -------------------------------------------------
        # MANUAL REVIEW / ESCALATION
        # -------------------------------------------------

        if action_type == "manual_review":

            return CommunicationPolicyDecision(
                decision="escalated",
                channel=None,
                template_name=None,
                template_version=None,
                reason=(
                    "Manual-review cases must not be "
                    "represented to the customer as "
                    "automatically resolved."
                ),
                allowed_variables=frozenset(),
            )

        # -------------------------------------------------
        # PARTIAL RECOVERY
        # -------------------------------------------------

        if (
            recovery_case_status
            == "partially_recovered"
            and payment_link_created
        ):

            return CommunicationPolicyDecision(
                decision="allowed",
                channel=channel,
                template_name="partial_payment_received",
                template_version="1.0",
                reason=(
                    "Partial payment has been received. "
                    "Communication may acknowledge the "
                    "amount received and provide the "
                    "remaining recovery option."
                ),
                allowed_variables=(
                    self.PARTIAL_RECOVERY_VARIABLES
                ),
            )

        # -------------------------------------------------
        # RECOVERED CASE
        # -------------------------------------------------

        if recovery_case_status == "recovered":

            if not recovery_confirmed:

                return CommunicationPolicyDecision(
                    decision="blocked",
                    channel=None,
                    template_name=None,
                    template_version=None,
                    reason=(
                        "Recovery success cannot be "
                        "communicated without provider "
                        "confirmation."
                    ),
                    allowed_variables=frozenset(),
                )

            return CommunicationPolicyDecision(
                decision="allowed",
                channel=channel,
                template_name="payment_recovered",
                template_version="1.0",
                reason=(
                    "Payment-provider confirmation "
                    "establishes successful recovery."
                ),
                allowed_variables=(
                    self.SUCCESS_VARIABLES
                ),
            )

        # -------------------------------------------------
        # FAILED RECOVERY ACTION
        # -------------------------------------------------

        if recovery_action_status == "failed":

            return CommunicationPolicyDecision(
                decision="allowed",
                channel=channel,
                template_name="payment_recovery",
                template_version="1.0",
                reason=(
                    "Recovery attempt failed. "
                    "Communication may explain the "
                    "unsuccessful attempt without "
                    "misrepresenting the case as resolved."
                ),
                allowed_variables=(
                    self.PAYMENT_RECOVERY_VARIABLES
                ),
            )

        # -------------------------------------------------
        # ALTERNATIVE PAYMENT METHOD
        # -------------------------------------------------

        if action_type == "alternative_payment_method":

            if payment_link_created:

                return CommunicationPolicyDecision(
                    decision="allowed",
                    channel=channel,
                    template_name="payment_recovery",
                    template_version="1.0",
                    reason=(
                        "Alternative payment method is "
                        "allowed and a secure Payment Link "
                        "is available. The message must not "
                        "claim that recovery has already "
                        "occurred."
                    ),
                    allowed_variables=(
                        self.PAYMENT_RECOVERY_VARIABLES
                    ),
                )

            return CommunicationPolicyDecision(
                decision="blocked",
                channel=None,
                template_name=None,
                template_version=None,
                reason=(
                    "An alternative payment method may "
                    "be communicated only when a secure "
                    "payment option is available."
                ),
                allowed_variables=frozenset(),
            )

        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------

        return CommunicationPolicyDecision(
            decision="blocked",
            channel=None,
            template_name=None,
            template_version=None,
            reason=(
                "No communication rule authorizes "
                "this recovery state."
            ),
            allowed_variables=frozenset(),
        )

    def validate_variables(
        self,
        variables: dict[str, object],
        allowed_variables: frozenset[str],
    ) -> None:
        """
        Ensure customer-facing communication cannot receive
        internal recovery information.
        """

        supplied = set(
            variables.keys()
        )

        forbidden = (
            supplied
            & self.INTERNAL_FIELDS
        )

        if forbidden:

            raise ValueError(
                "Communication contains internal "
                "fields that must not be exposed: "
                f"{sorted(forbidden)}"
            )

        unknown = (
            supplied
            - allowed_variables
        )

        if unknown:

            raise ValueError(
                "Communication contains variables "
                "not authorized by policy: "
                f"{sorted(unknown)}"
            )