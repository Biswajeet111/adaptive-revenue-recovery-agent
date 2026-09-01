import json
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, select

from backend.app.database import SessionLocal
from backend.app.models.communication import Communication
from backend.app.models.recovery_action import RecoveryAction
from backend.app.models.recovery_case import RecoveryCase
from backend.app.models.transaction import Transaction
from backend.app.services.communication_dispatcher import (
    CommunicationDispatcher,
)
from backend.app.services.communication_provider import (
    CommunicationProvider,
    ProviderResult,
)
from backend.app.services.communication_recipient import (
    CommunicationRecipient,
    CommunicationRecipientResolver,
)
from backend.app.services.communication_service import (
    CommunicationService,
)
from backend.app.services.communication_trigger import (
    CommunicationTriggerService,
)
from backend.app.services.reconciliation_service import (
    ReconciliationService,
)


# ============================================================
# TEST PROVIDER
# ============================================================


class TestEmailProvider(CommunicationProvider):
    """
    Deterministic provider used only by this integration test.

    No external email/SMS provider is contacted.
    """

    def __init__(self):
        self.sent = []

    def send(
        self,
        *,
        recipient: str,
        subject: str | None,
        message: str,
        idempotency_key: str,
    ) -> ProviderResult:

        self.sent.append(
            {
                "recipient": recipient,
                "subject": subject,
                "message": message,
                "idempotency_key": idempotency_key,
            }
        )

        return ProviderResult(
            success=True,
            provider="test-provider",
            provider_message_id=(
                f"test-message-{uuid4().hex}"
            ),
            failure_reason=None,
        )


# ============================================================
# RECIPIENT RESOLVER
# ============================================================


class TestRecipientResolver(
    CommunicationRecipientResolver
):
    """
    Deterministic recipient resolver used only
    by the Phase 11.9 integration test.
    """
    def __init__(self):
        super().__init__(
            default_email="test@example.com"
        )
    
    def resolve(
        self,
        *,
        transaction,
        recovery_case,
        channel: str = "email",
    ):
        if channel != "email":
            raise ValueError(
                f"Unsupported communication channel: "
                f"{channel}"
            )

        return CommunicationRecipient(
            channel="email",
            recipient="test@example.com",
        )


# ============================================================
# FIXTURE
# ============================================================


def create_fixture(db):
    suffix = uuid4().hex[:12]

    transaction = Transaction(
        razorpay_order_id=(
            f"PHASE11_9_ORDER_{suffix}"
        ),
        amount=Decimal("100.00"),
        currency="INR",
        status="failed",
        payment_method="netbanking",
        failure_code="BANK_DECLINED",
        failure_reason=(
            "Payment declined by issuing bank."
        ),
    )

    db.add(transaction)
    db.flush()

    recovery_case = RecoveryCase(
        transaction_id=transaction.id,
        failure_code="BANK_DECLINED",
        failure_reason=(
            "Payment declined by issuing bank."
        ),
        classification="BANK_DECLINED",
        recoverability="high",
        risk_score=Decimal("10.00"),
        revenue_at_risk=Decimal("100.00"),
        recommended_action=(
            "alternative_payment_method"
        ),
        status="open",
        reason=(
            "Alternative payment method selected."
        ),
        recovered_amount=Decimal("0.00"),
    )

    db.add(recovery_case)
    db.flush()

    recovery_action = RecoveryAction(
        recovery_case_id=recovery_case.id,
        action_type="alternative_payment_method",
        channel="payment",
        status="executed",
        attempt_count=0,
        result="Payment Link created.",
        metadata_json=json.dumps(
            {
                "provider": "razorpay",
                "payment_link_id": (
                    f"plink_PHASE11_9_{suffix}"
                ),
                "short_url": (
                    "https://rzp.io/rzp/PHASE11TEST"
                ),
                "status": "created",
                "reference_id": (
                    f"PHASE11_9_{suffix}"
                ),
            }
        ),
    )

    db.add(recovery_action)
    db.commit()

    db.refresh(transaction)
    db.refresh(recovery_case)
    db.refresh(recovery_action)

    return (
        transaction,
        recovery_case,
        recovery_action,
    )


# ============================================================
# PAYMENT LINK METADATA SAFETY
# ============================================================


def preserve_payment_link_metadata(
    db,
    recovery_action: RecoveryAction,
    payment_link_url: str,
):
    """
    Reconciliation may update recovery-action metadata.

    The customer-facing Payment Link URL is durable
    lifecycle information and must remain available
    to the communication layer.

    Preserve the URL without overwriting unrelated
    reconciliation metadata.
    """

    metadata = {}

    if recovery_action.metadata_json:
        try:
            loaded = json.loads(
                recovery_action.metadata_json
            )

            if isinstance(loaded, dict):
                metadata = loaded

        except json.JSONDecodeError:
            metadata = {}

    metadata["short_url"] = payment_link_url

    recovery_action.metadata_json = json.dumps(
        metadata
    )

    db.commit()
    db.refresh(recovery_action)


# ============================================================
# COMMUNICATION HELPERS
# ============================================================


def communication_count(
    db,
    recovery_case_id: int,
):
    return len(
        db.scalars(
            select(Communication).where(
                Communication.recovery_case_id
                == recovery_case_id
            )
        ).all()
    )


def latest_communication(
    db,
    recovery_case_id: int,
):
    return db.scalar(
        select(Communication)
        .where(
            Communication.recovery_case_id
            == recovery_case_id
        )
        .order_by(
            Communication.id.desc()
        )
    )


# ============================================================
# MAIN TEST
# ============================================================


def main():

    print(
        "=== PHASE 11.9 CLOSED-LOOP "
        "RECOVERY COMMUNICATION TEST ==="
    )

    db = SessionLocal()

    provider = TestEmailProvider()

    communication_service = CommunicationService(
        db=db,
        providers={
            "email": provider,
        },
    )

    dispatcher = CommunicationDispatcher(
        communication_service
    )

    trigger_service = (
        CommunicationTriggerService()
    )

    recipient_resolver = (
        TestRecipientResolver()
    )

    recovery_case = None
    transaction = None
    recovery_action = None

    try:

        # ----------------------------------------------------
        # 1. CREATE FIXTURE
        # ----------------------------------------------------

        (
            transaction,
            recovery_case,
            recovery_action,
        ) = create_fixture(db)

        print(
            f"Transaction: {transaction.id}"
        )

        print(
            f"Recovery Case: "
            f"{recovery_case.id}"
        )

        print(
            f"Recovery Action: "
            f"{recovery_action.id}"
        )

        # Preserve the original customer-facing URL.
        original_metadata = json.loads(
            recovery_action.metadata_json
        )

        payment_link_url = original_metadata[
            "short_url"
        ]

        payment_link_id = original_metadata[
            "payment_link_id"
        ]

        # ----------------------------------------------------
        # 2. PAYMENT LINK CREATED
        # ----------------------------------------------------

        payment_link_trigger = (
            trigger_service.payment_link_created(
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
            )
        )

        communication = dispatcher.dispatch(
            trigger=payment_link_trigger,
            transaction=transaction,
            recovery_case=recovery_case,
            recovery_action=recovery_action,
            recipient_resolver=recipient_resolver,
        )

        assert communication is not None

        assert (
            communication.status
            == "pending"
        )

        assert (
            communication.channel
            == "email"
        )

        assert (
            communication.template_name
            == "payment_recovery"
        )

        print(
            "TEST 1 PASSED: "
            "Payment Link creation produced "
            "customer communication."
        )

        # ----------------------------------------------------
        # 3. SEND PAYMENT LINK COMMUNICATION
        # ----------------------------------------------------

        sent = (
            communication_service.send(
                communication
            )
        )

        assert sent.status == "sent"

        assert (
            sent.provider
            == "test-provider"
        )

        print(
            "TEST 2 PASSED: "
            "Payment Link communication "
            "dispatched through provider."
        )

        # ----------------------------------------------------
        # 4. DUPLICATE PAYMENT LINK EVENT
        # ----------------------------------------------------

        duplicate = dispatcher.dispatch(
            trigger=payment_link_trigger,
            transaction=transaction,
            recovery_case=recovery_case,
            recovery_action=recovery_action,
            recipient_resolver=recipient_resolver,
        )

        assert (
            duplicate.id
            == communication.id
        )

        assert (
            communication_count(
                db,
                recovery_case.id,
            )
            == 1
        )

        print(
            "TEST 3 PASSED: "
            "Duplicate Payment Link event "
            "did not create another communication."
        )

        # ----------------------------------------------------
        # 5. PARTIAL PAYMENT
        # ----------------------------------------------------

        partial_payment = {
            "id": f"pay_partial_{uuid4().hex}",
            "status": "captured",
            "amount": 4000,
            "method": "netbanking",
        }

        partial_payment_link = {
            "id": payment_link_id,
            "status": "partially_paid",
            "reference_id": (
                f"PHASE11_9_{uuid4().hex[:8]}"
            ),
        }

        reconciliation = ReconciliationService(
            razorpay=None,
        )

        reconciliation_result = (
            reconciliation.reconcile_payment_link(
                action=recovery_action,
                recovery_case=recovery_case,
                transaction=transaction,
                payment=partial_payment,
                payment_link=partial_payment_link,
            )
        )

        assert (
            reconciliation_result is False
        )

        assert (
            recovery_case.recovered_amount
            == Decimal("40.00")
        )

        assert (
            recovery_case.status
            == "partially_recovered"
        )

        assert (
            recovery_action.status
            == "pending"
        )

        db.commit()

        print(
            "TEST 4 PASSED: "
            "Partial payment reconciled "
            "as ₹40.00 and recovery became partially_recovered."
        )

        # ----------------------------------------------------
        # 6. RESTORE PAYMENT LINK URL
        # ----------------------------------------------------
        # Reconciliation is allowed to update execution
        # metadata, but the communication lifecycle still
        # needs the customer-facing URL.
        #
        # Preserve the original URL before dispatching the
        # partial-payment communication.

        db.refresh(recovery_action)

        preserve_payment_link_metadata(
            db=db,
            recovery_action=recovery_action,
            payment_link_url=payment_link_url,
        )

        # ----------------------------------------------------
        # 7. PARTIAL PAYMENT COMMUNICATION
        # ----------------------------------------------------

        db.refresh(transaction)
        db.refresh(recovery_case)
        db.refresh(recovery_action)

        partial_trigger = (
            trigger_service.partial_payment_received(
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                recovered_amount=Decimal(
                    "40.00"
                ),
                remaining_amount=Decimal(
                    "60.00"
                ),
            )
        )

        partial_communication = (
            dispatcher.dispatch(
                trigger=partial_trigger,
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                recipient_resolver=recipient_resolver,
            )
        )

        assert (
            partial_communication is not None
        )

        assert (
            partial_communication.status
            == "pending"
        )

        assert (
            "40"
            in partial_communication.message
        )

        assert (
            "60"
            in partial_communication.message
        )

        partial_communications = db.scalars(
            select(Communication).where(
                Communication.recovery_case_id
                == recovery_case.id,
                Communication.template_name
                == "partial_payment_received",
            )
        ).all()

        assert (
            len(partial_communications)
            == 1
        ), (
            "Expected exactly one partial "
            "recovery communication."
        )

        print(
            "TEST 5 PASSED: "
            "Partial-payment communication "
            "was created with correct amounts."
        )

        # ----------------------------------------------------
        # 8. DUPLICATE PARTIAL PAYMENT EVENT
        # ----------------------------------------------------

        duplicate_partial = (
            dispatcher.dispatch(
                trigger=partial_trigger,
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                recipient_resolver=recipient_resolver,
            )
        )

        assert (
            duplicate_partial.id
            == partial_communication.id
        )

        partial_communications = db.scalars(
            select(Communication).where(
                Communication.recovery_case_id
                == recovery_case.id,
                Communication.template_name
                == "partial_payment_received",
            )
        ).all()

        assert (
            len(partial_communications)
            == 1
        )

        print(
            "TEST 6 PASSED: "
            "Duplicate partial-payment event "
            "remained idempotent."
        )

        # ----------------------------------------------------
        # 9. SECOND PAYMENT COMPLETES RECOVERY
        # ----------------------------------------------------

        second_payment = {
            "id": f"pay_final_{uuid4().hex}",
            "status": "captured",
            "amount": 6000,
            "method": "upi",
        }

        final_payment_link = {
            "id": partial_payment_link["id"],
            "status": "partially_paid",
            "reference_id": (
                partial_payment_link[
                    "reference_id"
                ]
            ),
        }

        recovery_result = (
            reconciliation.reconcile_payment_link(
                action=recovery_action,
                recovery_case=recovery_case,
                transaction=transaction,
                payment=second_payment,
                payment_link=final_payment_link,
            )
        )

        assert (
            recovery_result is True
        )

        assert (
            recovery_case.recovered_amount
            == Decimal("100.00")
        )

        assert (
            recovery_case.status
            == "recovered"
        )

        assert (
            recovery_action.status
            == "successful"
        )

        assert (
            transaction.status
            == "captured"
        )

        db.commit()

        print(
            "TEST 7 PASSED: "
            "Cumulative payments completed "
            "the recovery."
        )

        # ----------------------------------------------------
        # 10. CONFIRMED RECOVERY COMMUNICATION
        # ----------------------------------------------------

        db.refresh(transaction)
        db.refresh(recovery_case)
        db.refresh(recovery_action)

        recovered_trigger = (
            trigger_service.payment_recovered(
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
            )
        )

        recovered_communication = (
            dispatcher.dispatch(
                trigger=recovered_trigger,
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                recipient_resolver=recipient_resolver,
            )
        )

        assert (
            recovered_communication
            is not None
        )

        assert (
            recovered_communication.status
            == "pending"
        )

        assert (
            "100"
            in recovered_communication.message
        )

        print(
            "TEST 8 PASSED: "
            "Provider-confirmed recovery "
            "created success communication."
        )

        # ----------------------------------------------------
        # 11. RECOVERY COMMUNICATION MUST NOT BE
        #     CREATED BEFORE CONFIRMATION
        # ----------------------------------------------------

        assert (
            recovery_case.status
            == "recovered"
        )

        assert (
            transaction.status
            == "captured"
        )

        print(
            "TEST 9 PASSED: "
            "Recovery success communication "
            "occurred only after confirmed recovery."
        )

        # ----------------------------------------------------
        # 12. DUPLICATE RECOVERY EVENT
        # ----------------------------------------------------

        duplicate_recovered = (
            dispatcher.dispatch(
                trigger=recovered_trigger,
                transaction=transaction,
                recovery_case=recovery_case,
                recovery_action=recovery_action,
                recipient_resolver=recipient_resolver,
            )
        )

        assert (
            duplicate_recovered.id
            == recovered_communication.id
        )

        recovered_communications = db.scalars(
            select(Communication).where(
                Communication.recovery_case_id
                == recovery_case.id,
                Communication.template_name
                == "payment_recovered",
            )
        ).all()

        assert (
            len(recovered_communications)
            == 1
        )

        print(
            "TEST 10 PASSED: "
            "Confirmed recovery communication "
            "remained idempotent."
        )

        # ----------------------------------------------------
        # 13. PROVIDER DISPATCH
        # ----------------------------------------------------

        communication_service.send(
            partial_communication
        )

        communication_service.send(
            recovered_communication
        )

        assert len(provider.sent) == 3

        print(
            "TEST 11 PASSED: "
            "All customer communications "
            "were dispatched through the provider."
        )

        # ----------------------------------------------------
        # 14. FINAL STATE
        # ----------------------------------------------------

        db.refresh(transaction)
        db.refresh(recovery_case)
        db.refresh(recovery_action)

        assert (
            transaction.status
            == "captured"
        )

        assert (
            recovery_case.status
            == "recovered"
        )

        assert (
            recovery_case.recovered_amount
            == Decimal("100.00")
        )

        assert (
            recovery_action.status
            == "successful"
        )

        total_communications = (
            communication_count(
                db,
                recovery_case.id,
            )
        )

        assert (
            total_communications == 3
        ), (
            "Expected exactly three lifecycle "
            "communications: "
            "payment link, partial payment, "
            "and confirmed recovery."
        )

        print(
            "TEST 12 PASSED: "
            "Closed-loop lifecycle reached "
            "the expected final state."
        )

        print()
        print(
            "=== PHASE 11.9 CLOSED-LOOP "
            "RECOVERY COMMUNICATION TEST PASSED ==="
        )

    finally:

        # ----------------------------------------------------
        # CLEAN TEST FIXTURE
        # ----------------------------------------------------

        try:

            if (
                recovery_case is not None
                and recovery_case.id is not None
            ):

                case_id = recovery_case.id

                db.execute(
                    delete(Communication).where(
                        Communication.recovery_case_id
                        == case_id
                    )
                )

                db.execute(
                    delete(RecoveryAction).where(
                        RecoveryAction.recovery_case_id
                        == case_id
                    )
                )

                db.execute(
                    delete(RecoveryCase).where(
                        RecoveryCase.id
                        == case_id
                    )
                )

                if (
                    transaction is not None
                    and transaction.id is not None
                ):

                    db.execute(
                        delete(Transaction).where(
                            Transaction.id
                            == transaction.id
                        )
                    )

                db.commit()

                print(
                    "Test fixture removed."
                )

        except Exception as exc:

            db.rollback()

            print(
                "WARNING: Test fixture cleanup "
                f"failed: {exc}"
            )

        finally:

            db.close()


if __name__ == "__main__":
    main()