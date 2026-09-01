import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.signature_service import (
    verify_razorpay_signature,
)
from backend.app.services.webhook_service import WebhookService


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(
        default=None,
        alias="X-Razorpay-Signature",
    ),
    db: Session = Depends(get_db),
):
    # =========================================================
    # 1. Read raw request body
    # =========================================================

    raw_body = await request.body()

    if not raw_body:
        raise HTTPException(
            status_code=400,
            detail="Empty webhook body",
        )

    # =========================================================
    # 2. Validate signature
    # =========================================================

    if not x_razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay webhook signature",
        )

    if not verify_razorpay_signature(
        raw_body,
        x_razorpay_signature,
        settings.razorpay_webhook_secret,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature",
        )

    # =========================================================
    # 3. Parse JSON
    # =========================================================

    try:
        payload = json.loads(raw_body)

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    # =========================================================
    # 4. Extract event information
    # =========================================================

    event_type = payload.get(
        "event"
    )

    if not event_type:

        raise HTTPException(
            status_code=400,
            detail="Missing event type",
        )

    event_id = request.headers.get(
        "X-Razorpay-Event-Id"
    )

    if not event_id:

        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay event ID",
        )

    webhook_service = WebhookService(
        db,
        enable_communications=True,
    )

    # =========================================================
    # 5. EVENT-LEVEL IDEMPOTENCY
    # =========================================================
    #
    # If the event already exists:
    #
    # processed = True
    #     -> permanently ignore duplicate
    #
    # processed = False
    #     -> previous processing failed/interrupted
    #     -> allow retry
    #
    # This is important because Razorpay may retry
    # webhook delivery after a processing failure.
    # =========================================================

    existing_event = (
        webhook_service.get_event(
            event_id
        )
    )

    if existing_event is not None:

        if existing_event.processed:

            return {
                "success": True,
                "status": "duplicate_ignored",
                "event_id": event_id,
            }

        # Existing event was never successfully processed.
        # Reuse it rather than inserting a duplicate row.

        event = existing_event

    else:

        try:

            event = webhook_service.store_event(
                event_id=event_id,
                event_type=event_type,
                payload=payload,
                signature=x_razorpay_signature,
            )

        except Exception as exc:

            db.rollback()

            print(
                f"WEBHOOK STORAGE ERROR | "
                f"event_id={event_id} | "
                f"event_type={event_type} | "
                f"error={type(exc).__name__}: {exc}"
            )

            raise HTTPException(
                status_code=500,
                detail="Webhook storage failed",
            )

    # =========================================================
    # 6. PROCESS EVENT
    # =========================================================

    try:

        if event_type in {
            "payment.failed",
            "payment.authorized",
            "payment.captured",
        }:

            webhook_service.process_payment_event(
                event
            )

        elif event_type in {
            "payment_link.paid",
            "payment_link.partially_paid",
            "payment_link.expired",
            "payment_link.cancelled",
        }:

            webhook_service.process_payment_link_event(
                event
            )

        elif event_type == "order.paid":

            event.processed = True

            event.processed_at = (
                datetime.now(timezone.utc)
            )

            db.flush()

        else:

            # Unknown/unimplemented event types are safely
            # recorded so they do not repeatedly trigger
            # webhook retries.

            event.processed = True

            event.processed_at = (
                datetime.now(timezone.utc)
            )

            db.flush()

        # =====================================================
        # 7. COMMIT ONLY AFTER SUCCESSFUL PROCESSING
        # =====================================================

        db.commit()

    except Exception as exc:

        db.rollback()

        print(
            f"WEBHOOK PROCESSING ERROR | "
            f"event_id={event_id} | "
            f"event_type={event_type} | "
            f"error={type(exc).__name__}: {exc}"
        )

        # IMPORTANT:
        #
        # Because the transaction was rolled back, the
        # WebhookEvent remains unprocessed in the database.
        #
        # A Razorpay retry can therefore process it again.

        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed",
        )

    # =========================================================
    # 8. SUCCESS RESPONSE
    # =========================================================

    return {
        "success": True,
        "status": "processed",
        "event_id": event_id,
        "event": event_type,
    }